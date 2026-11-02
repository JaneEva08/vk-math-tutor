"""Сервис ответов модели и восстановление после сетевых ошибок."""

import logging
from abc import ABC, abstractmethod

from services.openai_provider import OpenAIProvider

from config.settings import Settings
from models.user_data import ChatMessage

logger = logging.getLogger(__name__)

FALLBACK_REPLY = "😔 Не получилось получить ответ от нейросети. Попробуй ещё раз чуть позже."


class AIError(Exception):
    pass


class AIProvider(ABC):
    """Интерфейс провайдера: позже можно подключить другие модели."""

    model: str

    @abstractmethod
    async def generate(self, system_prompt: str, history: list[ChatMessage], user_message: str) -> str: ...


class AIService:
    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    @classmethod
    def from_settings(cls, settings: Settings) -> "AIService":
        return cls(OpenAIProvider(settings.openai_api_key, settings.openai_model, settings.openai_base_url))

    @property
    def model_name(self) -> str:
        return self._provider.model

    async def reply(self, system_prompt: str, history: list[ChatMessage], user_message: str) -> tuple[str, bool]:
        """Возвращает (текст, ok). При ошибке API — (fallback, False), история не портится."""
        try:
            return await self._provider.generate(system_prompt, history, user_message), True
        except AIError:
            logger.warning("Ошибка запроса к LLM")
            return FALLBACK_REPLY, False
