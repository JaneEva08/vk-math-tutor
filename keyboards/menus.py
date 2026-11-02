"""Клавиатуры ВКонтакте. Все кнопки текстовые с payload {"cmd": ..., "id": ...}."""

from vkbottle import Keyboard, KeyboardButtonColor, Text

from config.prompts import MODES, get_mode
from models.user_data import UserData

MAX_DIALOGS_IN_LIST = 6


def _btn(label: str, cmd: str, arg: str | None = None) -> Text:
    payload = {"cmd": cmd}
    if arg is not None:
        payload["id"] = arg
    return Text(label[:40], payload)


def main_menu(*, inline: bool = False) -> str:
    kb = Keyboard(one_time=False, inline=inline)
    kb.add(_btn("📚 Новая тема", "topic"), KeyboardButtonColor.PRIMARY)
    kb.add(_btn("✍️ Тест по теме", "test"))
    kb.row()
    kb.add(_btn("💡 Объясни проще", "simpler"))
    kb.row()
    kb.add(_btn("➕ Новый диалог", "new"), KeyboardButtonColor.POSITIVE)
    kb.add(_btn("📋 Список диалогов", "list"))
    kb.row()
    kb.add(_btn("⚙️ Настройки", "settings"))
    kb.add(_btn("🎭 Сменить режим", "modes"))
    kb.row()
    kb.add(_btn("❓ Помощь", "help"))
    return kb.get_json()


def start_button() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(_btn("Начать", "start"), KeyboardButtonColor.PRIMARY)
    return kb.get_json()


def dialog_list(user: UserData) -> str:
    kb = Keyboard(one_time=False, inline=False)
    for dialog in user.dialogs[-MAX_DIALOGS_IN_LIST:]:
        active = dialog.id == user.active_dialog_id
        label = f"{'✅ ' if active else ''}{dialog.title}"
        kb.add(_btn(label, "switch", dialog.id), KeyboardButtonColor.POSITIVE if active else KeyboardButtonColor.SECONDARY)
        kb.row()
    active_id = user.active_dialog_id
    kb.add(_btn("✏️ Переименовать", "rename", active_id))
    kb.add(_btn("🗑 Удалить", "delete", active_id), KeyboardButtonColor.NEGATIVE)
    kb.row()
    kb.add(_btn("➕ Новый", "new"))
    kb.add(_btn("🏠 Меню", "menu"))
    return kb.get_json()


def mode_list(current_mode_id: str) -> str:
    kb = Keyboard(one_time=False, inline=False)
    modes = list(MODES.values())
    for i, mode in enumerate(modes):
        color = KeyboardButtonColor.POSITIVE if mode.id == current_mode_id else KeyboardButtonColor.SECONDARY
        kb.add(_btn(mode.title, "set_mode", mode.id), color)
        if i % 2 == 1 and i != len(modes) - 1:
            kb.row()
    kb.row()
    kb.add(_btn("◀️ Назад", "menu"))
    return kb.get_json()


def settings_menu() -> str:
    kb = Keyboard(one_time=False, inline=False)
    kb.add(_btn("🎓 Изменить класс", "grade"))
    kb.row()
    kb.add(_btn("🎭 Выбрать режим", "modes"))
    kb.row()
    kb.add(_btn("🧹 Очистить историю", "clear"), KeyboardButtonColor.NEGATIVE)
    kb.row()
    kb.add(_btn("🏠 Главное меню", "menu"))
    return kb.get_json()


def chat_actions() -> str:
    """Inline-кнопки под ответом модели."""
    kb = Keyboard(inline=True)
    kb.add(_btn("🎭 Режим", "modes"))
    kb.add(_btn("🧹 Очистить", "clear"))
    kb.add(_btn("🏠 Меню", "menu"))
    return kb.get_json()


def mode_title(mode_id: str) -> str:
    return get_mode(mode_id).title
