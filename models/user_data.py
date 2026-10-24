"""Модели данных пользователя: сообщения, диалоги, профиль."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from config.prompts import DEFAULT_MODE_ID


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ChatMessage:
    role: str  # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {"role": self.role, "content": self.content, "timestamp": self.timestamp}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChatMessage:
        return cls(data["role"], data["content"], data.get("timestamp", _now()))


@dataclass
class Dialog:
    title: str
    mode_id: str = DEFAULT_MODE_ID
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[ChatMessage] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "mode_id": self.mode_id,
            "messages": [m.to_dict() for m in self.messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Dialog:
        return cls(
            title=data["title"],
            mode_id=data.get("mode_id", DEFAULT_MODE_ID),
            id=data["id"],
            messages=[ChatMessage.from_dict(m) for m in data.get("messages", [])],
        )


@dataclass
class UserData:
    user_id: int
    dialogs: list[Dialog] = field(default_factory=list)
    active_dialog_id: str = ""
    settings: dict[str, Any] = field(default_factory=dict)

    @property
    def active_dialog(self) -> Dialog:
        for dialog in self.dialogs:
            if dialog.id == self.active_dialog_id:
                return dialog
        return self.dialogs[0]

    def find(self, dialog_id: str) -> Dialog | None:
        return next((d for d in self.dialogs if d.id == dialog_id), None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "dialogs": [d.to_dict() for d in self.dialogs],
            "active_dialog_id": self.active_dialog_id,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserData:
        return cls(
            user_id=data["user_id"],
            dialogs=[Dialog.from_dict(d) for d in data.get("dialogs", [])],
            active_dialog_id=data.get("active_dialog_id", ""),
            settings=data.get("settings", {}),
        )

    @classmethod
    def new(cls, user_id: int) -> UserData:
        first = Dialog(title="Основной диалог")
        return cls(user_id=user_id, dialogs=[first], active_dialog_id=first.id)
