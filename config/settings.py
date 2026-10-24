"""Настройки приложения из переменных окружения (.env)."""

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    vk_token: str
    proxy_api_key: str
    gemini_model: str = "gemini-3.1-flash-lite"
    gemini_base_url: str = "https://api.proxyapi.ru/google"
    max_message_length: int = 4000
    max_history_messages: int = 100
    users_dir: Path = ROOT_DIR / "users"
    log_level: str = "INFO"

    def validate(self) -> None:
        missing = [
            name
            for name, value in (("VK_TOKEN", self.vk_token), ("PROXY_API_KEY", self.proxy_api_key))
            if not value
        ]
        if missing:
            raise RuntimeError(f"В .env не заполнены переменные: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    load_dotenv(ROOT_DIR / ".env")
    users_dir = Path(os.getenv("USERS_DIR", "users"))
    if not users_dir.is_absolute():
        users_dir = ROOT_DIR / users_dir
    return Settings(
        vk_token=os.getenv("VK_TOKEN", ""),
        proxy_api_key=os.getenv("PROXY_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        gemini_base_url=os.getenv("GEMINI_BASE_URL", "https://api.proxyapi.ru/google"),
        max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "4000")),
        max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "100")),
        users_dir=users_dir,
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
