"""Краткосрочная память: последние N сообщений активного диалога."""

from models.user_data import ChatMessage, Dialog


class MemoryManager:
    def __init__(self, max_messages: int = 100) -> None:
        self._max = max_messages

    def add(self, dialog: Dialog, role: str, content: str) -> None:
        dialog.messages.append(ChatMessage(role, content))
        if len(dialog.messages) > self._max:
            del dialog.messages[: len(dialog.messages) - self._max]

    def context(self, dialog: Dialog) -> list[ChatMessage]:
        return dialog.messages[-self._max :]

    def clear(self, dialog: Dialog) -> None:
        dialog.messages.clear()
