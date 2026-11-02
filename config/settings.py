"""Настройки приложения из переменных окружения (.env)."""

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    vk_token: str = field(repr=False)
    openai_api_key: str = field(repr=False)
    openai_model: str = "gpt-6-luna"
    openai_base_url: str = "https://aiprimetech.io/v1"
    vk_group_id: int = 240579943
    max_message_length: int = 4000
    max_history_messages: int = 100
    users_dir: Path = ROOT_DIR / "users"
    log_level: str = "INFO"

    def validate(self) -> None:
        missing = [
            name
            for name, value in (("VK_TOKEN", self.vk_token), ("OPENAI_API_KEY", self.openai_api_key))
            if not value
        ]
        if missing:
            raise RuntimeError(f"В .env не заполнены переменные: {', '.join(missing)}")
        if not 2 <= self.max_history_messages <= 100 or not 100 <= self.max_message_length <= 4000:
            raise RuntimeError("История: 2–100 сообщений; длина: 100–4000 символов")


@lru_cache
def get_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    users_dir = Path(os.getenv("USERS_DIR", "users"))
    if not users_dir.is_absolute():
        users_dir = ROOT_DIR / users_dir
    return Settings(
        vk_token=os.getenv("VK_TOKEN", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-6-luna"),
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://aiprimetech.io/v1"),
        vk_group_id=int(os.getenv("VK_GROUP_ID", "240579943")),
        max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "4000")),
        max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "100")),
        users_dir=users_dir,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
