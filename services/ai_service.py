"""Работа с LLM: провайдер Gemini через ProxyAPI и централизованный AIService."""

import logging
from abc import ABC, abstractmethod

from google import genai
from google.genai import types

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


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.model = model
        self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(base_url=base_url))

    async def generate(self, system_prompt: str, history: list[ChatMessage], user_message: str) -> str:
        contents = [
            types.Content(
                role="model" if m.role == "assistant" else "user",
                parts=[types.Part(text=m.content)],
            )
            for m in history
        ]
        contents.append(types.Content(role="user", parts=[types.Part(text=user_message)]))
        try:
            response = await self._client.aio.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(system_instruction=system_prompt),
            )
        except Exception as exc:  # сеть, лимиты, ошибки API
            raise AIError(str(exc)) from exc
        text = (response.text or "").strip()
        if not text:
            raise AIError("Пустой ответ модели")
        return text


class AIService:
    def __init__(self, provider: AIProvider) -> None:
        self._provider = provider

    @classmethod
    def from_settings(cls, settings: Settings) -> "AIService":
        return cls(GeminiProvider(settings.proxy_api_key, settings.gemini_model, settings.gemini_base_url))

    @property
    def model_name(self) -> str:
        return self._provider.model

    async def reply(self, system_prompt: str, history: list[ChatMessage], user_message: str) -> tuple[str, bool]:
        """Возвращает (текст, ok). При ошибке API — (fallback, False), история не портится."""
        try:
            return await self._provider.generate(system_prompt, history, user_message), True
        except AIError:
            logger.exception("Ошибка запроса к LLM")
            return FALLBACK_REPLY, False
