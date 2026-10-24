"""Имитация набора текста («бот печатает…») пока идёт запрос к модели."""

import asyncio
import contextlib
import logging

from vkbottle import API

logger = logging.getLogger(__name__)


class TypingIndicator:
    def __init__(self, api: API, peer_id: int, interval: float = 4.0) -> None:
        self._api = api
        self._peer_id = peer_id
        self._interval = interval
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        while True:
            try:
                await self._api.messages.set_activity(peer_id=self._peer_id, type="typing")
            except Exception:
                logger.debug("Не удалось отправить статус набора", exc_info=True)
            await asyncio.sleep(self._interval)

    async def __aenter__(self) -> "TypingIndicator":
        self._task = asyncio.create_task(self._run())
        return self

    async def __aexit__(self, *exc) -> None:
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
