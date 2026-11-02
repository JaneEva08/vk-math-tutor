import json
from types import SimpleNamespace

import pytest

from bot.handlers import BotHandlers
from config.settings import Settings
from models.user_data import UserData
from services.ai_service import FALLBACK_REPLY, AIError, AIProvider, AIService
from services.dialog_service import DialogError, DialogService
from storage.json_storage import JsonStorage
from storage.memory_manager import MemoryManager
from utils.text import split_message, strip_markdown


class FakeProvider(AIProvider):
    model = "fake-model"

    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    async def generate(self, system_prompt, history, user_message):
        self.calls.append((system_prompt, [m.content for m in history], user_message))
        if self.fail:
            raise AIError("boom")
        return f"**ответ** на {user_message}"


class FakeMessage:
    def __init__(self, text="", payload=None, user_id=1):
        self.text = text
        self.payload = json.dumps(payload) if payload else None
        self.from_id = user_id
        self.peer_id = user_id
        self.sent = []
        self.keyboards = []
        activity = SimpleNamespace(set_activity=self._noop)
        self.ctx_api = SimpleNamespace(messages=activity)

    @staticmethod
    async def _noop(**kwargs):
        return 1

    async def answer(self, text, keyboard=None):
        self.sent.append(text)
        self.keyboards.append(keyboard)


@pytest.fixture
def env(tmp_path):
    settings = Settings(vk_token="t", openai_api_key="k", users_dir=tmp_path, max_message_length=100)
    provider = FakeProvider()
    storage = JsonStorage(tmp_path)
    handlers = BotHandlers(settings, storage, DialogService(), MemoryManager(100), AIService(provider))
    return SimpleNamespace(handlers=handlers, storage=storage, provider=provider, tmp=tmp_path)


def test_memory_trims_to_limit():
    user = UserData.new(1)
    memory = MemoryManager(5)
    for i in range(12):
        memory.add(user.active_dialog, "user", str(i))
    assert [m.content for m in memory.context(user.active_dialog)] == ["7", "8", "9", "10", "11"]


def test_dialog_service_rules():
    user, svc = UserData.new(1), DialogService()
    with pytest.raises(DialogError):
        svc.delete(user, user.active_dialog_id)
    second = svc.create(user)
    assert user.active_dialog_id == second.id
    svc.set_mode(user, "teacher")
    assert second.mode_id == "teacher" and user.dialogs[0].mode_id == "math"
    svc.delete(user, second.id)
    assert len(user.dialogs) == 1 and user.active_dialog_id == user.dialogs[0].id
    with pytest.raises(DialogError):
        svc.set_mode(user, "nope")


def test_text_helpers():
    assert strip_markdown("### Заг\n**жир** и `код`\n* пункт") == "Заг\nжир и код\n- пункт"
    parts = split_message("слово " * 20, 30)
    assert all(len(p) <= 30 for p in parts) and " ".join(parts).split() == ["слово"] * 20


async def test_ai_service_fallback():
    text, ok = await AIService(FakeProvider(fail=True)).reply("s", [], "hi")
    assert (text, ok) == (FALLBACK_REPLY, False)


async def test_chat_flow_persists_context_and_modes(env):
    h = env.handlers
    await h.on_message(FakeMessage(payload={"cmd": "set_mode", "id": "assistant"}))
    m1 = FakeMessage("привет")
    await h.on_message(m1)
    assert m1.sent == ["ответ на привет"]  # markdown убран

    await h.on_message(FakeMessage(payload={"cmd": "set_mode", "id": "programmer"}))
    await h.on_message(FakeMessage("ещё"))
    system, history, _ = env.provider.calls[-1]
    assert "программист" in system and history == ["привет", "ответ на привет"]

    data = json.loads((env.tmp / "1.json").read_text(encoding="utf-8"))
    assert data["dialogs"][0]["mode_id"] == "programmer"
    assert [m["role"] for m in data["dialogs"][0]["messages"]] == ["user", "assistant"] * 2


async def test_dialogs_are_isolated_and_rename(env):
    h = env.handlers
    await h.on_message(FakeMessage(payload={"cmd": "set_mode", "id": "assistant"}))
    await h.on_message(FakeMessage("первый"))
    await h.on_message(FakeMessage(payload={"cmd": "new"}))
    await h.on_message(FakeMessage(payload={"cmd": "set_mode", "id": "assistant"}))
    await h.on_message(FakeMessage("второй"))
    assert env.provider.calls[-1][1] == []  # контекст не переносится

    user = await env.storage.load(1)
    await h.on_message(FakeMessage(payload={"cmd": "rename", "id": user.active_dialog_id}))
    await h.on_message(FakeMessage("Рецепты"))
    assert (await env.storage.load(1)).active_dialog.title == "Рецепты"


async def test_validation_and_delete_last(env):
    h = env.handlers
    empty, long_ = FakeMessage("  "), FakeMessage("x" * 101)
    await h.on_message(empty)
    await h.on_message(long_)
    assert "слишком длинное" in long_.sent[0] and not env.provider.calls
    user = await env.storage.load(1)
    deleting = FakeMessage(payload={"cmd": "delete", "id": user.active_dialog_id})
    await h.on_message(deleting)
    assert "Нельзя удалить единственный диалог" in deleting.sent[0]


async def test_failed_ai_does_not_pollute_history(env):
    await env.handlers.on_message(FakeMessage(payload={"cmd": "set_mode", "id": "assistant"}))
    env.provider.fail = True
    m = FakeMessage("привет")
    await env.handlers.on_message(m)
    assert m.sent == [FALLBACK_REPLY]
    assert (await env.storage.load(1)).active_dialog.messages == []


async def test_menu_return_shows_dialog_list_inline(env):
    message = FakeMessage(payload={"cmd": "menu"})
    await env.handlers.on_message(message)
    keyboard = json.loads(message.keyboards[-1])
    assert keyboard["inline"] is True
    commands = [b["action"]["payload"]["cmd"] for row in keyboard["buttons"] for b in row]
    assert "list" in commands and "new" in commands
