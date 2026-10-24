"""Менеджер диалогов: создание, переключение, переименование, удаление, режимы."""

from config.prompts import MODES
from models.user_data import Dialog, UserData

MAX_TITLE_LENGTH = 40


class DialogError(Exception):
    """Ошибка бизнес-логики диалогов (текст безопасно показывать пользователю)."""


class DialogService:
    def create(self, user: UserData, title: str | None = None) -> Dialog:
        dialog = Dialog(title=title or f"Диалог {len(user.dialogs) + 1}")
        user.dialogs.append(dialog)
        user.active_dialog_id = dialog.id
        return dialog

    def switch(self, user: UserData, dialog_id: str) -> Dialog:
        dialog = user.find(dialog_id)
        if dialog is None:
            raise DialogError("Диалог не найден")
        user.active_dialog_id = dialog.id
        return dialog

    def rename(self, user: UserData, dialog_id: str, title: str) -> Dialog:
        title = title.strip()[:MAX_TITLE_LENGTH]
        if not title:
            raise DialogError("Название не может быть пустым")
        dialog = user.find(dialog_id)
        if dialog is None:
            raise DialogError("Диалог не найден")
        dialog.title = title
        return dialog

    def delete(self, user: UserData, dialog_id: str) -> None:
        if len(user.dialogs) <= 1:
            raise DialogError("Нельзя удалить единственный диалог")
        dialog = user.find(dialog_id)
        if dialog is None:
            raise DialogError("Диалог не найден")
        user.dialogs.remove(dialog)
        if user.active_dialog_id == dialog_id:
            user.active_dialog_id = user.dialogs[0].id

    def set_mode(self, user: UserData, mode_id: str) -> Dialog:
        if mode_id not in MODES:
            raise DialogError("Неизвестный режим")
        dialog = user.active_dialog
        dialog.mode_id = mode_id  # меняется только текущий диалог
        return dialog
