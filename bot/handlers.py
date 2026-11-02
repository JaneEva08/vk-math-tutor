"""Обработчики сообщений ВКонтакте. Логика AI и логика VK разделены через сервисы."""

import json
import logging
from typing import Any

from vkbottle.bot import Message

from bot import messages as T
from config.prompts import get_mode
from config.settings import Settings
from keyboards import menus
from models.user_data import UserData
from services.ai_service import AIService
from services.dialog_service import DialogError, DialogService
from services.tutor_service import prepare_topic, study_context
from storage.json_storage import JsonStorage
from storage.memory_manager import MemoryManager
from utils.text import split_message, strip_markdown
from utils.typing_indicator import TypingIndicator

logger = logging.getLogger(__name__)

START_WORDS = {"начать", "/start", "start"}
MENU_WORDS = {"меню", "/menu"}


class BotHandlers:
    def __init__(
        self,
        settings: Settings,
        storage: JsonStorage,
        dialogs: DialogService,
        memory: MemoryManager,
        ai: AIService,
    ) -> None:
        self._settings = settings
        self._storage = storage
        self._dialogs = dialogs
        self._memory = memory
        self._ai = ai

    # --- входная точка -------------------------------------------------
    async def on_message(self, message: Message) -> None:
        user_id = message.from_id
        # лок на пользователя: сообщения одного человека обрабатываются по очереди
        async with self._storage.lock(user_id):
            user = await self._storage.load(user_id)
            try:
                changed = await self._dispatch(message, user)
            except DialogError as exc:
                await message.answer(f"⚠️ {exc}")
                return
            except Exception:
                logger.error("Ошибка обработки сообщения: user_id=%s", user_id)
                await message.answer(T.ERROR)
                return
            if changed:
                await self._storage.save(user)

    async def _dispatch(self, message: Message, user: UserData) -> bool:
        payload = self._parse_payload(message.payload)
        if payload:
            user.settings.pop("pending_rename", None)
            return await self._command(message, user, payload.get("cmd", ""), payload.get("id"))

        text = (message.text or "").strip()
        lowered = text.lower()
        if not text:
            await message.answer(T.EMPTY)
            return False
        if lowered in START_WORDS:
            return await self._command(message, user, "start", None)
        if lowered in MENU_WORDS:
            return await self._command(message, user, "menu", None)
        if (rename_id := user.settings.pop("pending_rename", None)) is not None:
            dialog = self._dialogs.rename(user, rename_id, text)
            await message.answer(T.RENAMED.format(title=dialog.title), keyboard=menus.main_menu())
            return True
        if len(text) > self._settings.max_message_length:
            await message.answer(T.TOO_LONG.format(limit=self._settings.max_message_length))
            return False
        return await self._chat(message, user, text)

    @staticmethod
    def _parse_payload(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    # --- команды (кнопки) ---------------------------------------------
    async def _command(self, message: Message, user: UserData, cmd: str, arg: str | None) -> bool:
        dialog = user.active_dialog
        if cmd == "start":
            await message.answer(T.START, keyboard=menus.main_menu())
        elif cmd == "menu":
            await message.answer(T.MENU, keyboard=menus.main_menu(inline=True))
        elif cmd == "help":
            await message.answer(T.HELP, keyboard=menus.main_menu())
        elif cmd == "new":
            created = self._dialogs.create(user)
            await message.answer(T.DIALOG_CREATED.format(title=created.title), keyboard=menus.main_menu())
            return True
        elif cmd == "list":
            await message.answer(self._render_list(user), keyboard=menus.dialog_list(user))
        elif cmd == "switch":
            switched = self._dialogs.switch(user, arg or "")
            await message.answer(
                T.DIALOG_SWITCHED.format(
                    title=switched.title, mode=menus.mode_title(switched.mode_id), count=len(switched.messages)
                ),
                keyboard=menus.main_menu(),
            )
            return True
        elif cmd == "rename":
            target = user.find(arg or "") or dialog
            user.settings["pending_rename"] = target.id
            await message.answer(T.RENAME_PROMPT.format(title=target.title))
            return True
        elif cmd == "delete":
            self._dialogs.delete(user, arg or "")
            await message.answer(T.DIALOG_DELETED.format(title=user.active_dialog.title), keyboard=menus.dialog_list(user))
            return True
        elif cmd == "modes":
            await message.answer(T.MODE_CHOOSE, keyboard=menus.mode_list(dialog.mode_id))
        elif cmd == "set_mode":
            updated = self._dialogs.set_mode(user, arg or "")
            await message.answer(
                T.MODE_SET.format(mode=menus.mode_title(updated.mode_id), title=updated.title),
                keyboard=menus.main_menu(),
            )
            return True
        elif cmd == "settings":
            await message.answer(
                T.SETTINGS.format(
                    title=dialog.title,
                    mode=menus.mode_title(dialog.mode_id),
                    model=self._ai.model_name,
                    count=len(dialog.messages),
                ),
                keyboard=menus.settings_menu(),
            )
        elif cmd == "clear":
            self._memory.clear(dialog)
            await message.answer(T.HISTORY_CLEARED.format(title=dialog.title), keyboard=menus.main_menu())
            return True
        elif cmd == "topic":
            self._memory.clear(dialog)
            dialog.study.clear()
            dialog.mode_id = "math"
            await message.answer("Какую новую тему разберём? Напиши её название.", keyboard=menus.main_menu())
            return True
        elif cmd == "grade":
            user.settings.pop("grade", None)
            self._memory.clear(dialog)
            dialog.study.clear()
            dialog.mode_id = "math"
            await message.answer("В каком ты классе? Напиши число от 1 до 11.")
            return True
        elif cmd in {"test", "simpler"}:
            if dialog.mode_id != "math" or not dialog.study.get("topic"):
                await message.answer("Сначала выбери режим репетитора и напиши класс и тему.")
                return False
            request = "Давай короткий тест по теме, по одному вопросу." if cmd == "test" else "Объясни текущий шаг проще, на другом примере."
            return await self._chat(message, user, request)
        else:
            await message.answer(T.MENU, keyboard=menus.main_menu())
        return False

    @staticmethod
    def _render_list(user: UserData) -> str:
        lines = ["📋 Ваши диалоги:", ""]
        for i, d in enumerate(user.dialogs, 1):
            mark = " ✅" if d.id == user.active_dialog_id else ""
            lines.append(f"{i}. {d.title}{mark}\n   Режим: {menus.mode_title(d.mode_id)} | Сообщений: {len(d.messages)}")
        return "\n".join(lines)

    # --- общение с моделью ---------------------------------------------
    async def _chat(self, message: Message, user: UserData, text: str) -> bool:
        dialog = user.active_dialog
        system_prompt = get_mode(dialog.mode_id).system_prompt
        if dialog.mode_id == "math":
            question = prepare_topic(user, text)
            if question:
                await message.answer(question, keyboard=menus.main_menu())
                return True
            system_prompt += study_context(user)
        history = self._memory.context(dialog)

        async with TypingIndicator(message.ctx_api, message.peer_id):
            answer, ok = await self._ai.reply(system_prompt, history, text)

        answer = strip_markdown(answer) if ok else answer
        if ok:
            self._memory.add(dialog, "user", text)
            self._memory.add(dialog, "assistant", answer)
            if dialog.mode_id == "math":
                from datetime import datetime, timezone
                dialog.study["last_activity"] = datetime.now(timezone.utc).isoformat()
                dialog.study["exchanges"] = dialog.study.get("exchanges", 0) + 1

        chunks = split_message(answer, self._settings.max_message_length)
        for i, chunk in enumerate(chunks):
            last = i == len(chunks) - 1
            await message.answer(chunk, keyboard=menus.chat_actions() if last else None)
        return ok or dialog.mode_id == "math"
