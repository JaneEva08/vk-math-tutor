"""JSON-хранилище: отдельный файл users/<user_id>.json на пользователя."""

import asyncio
import json
import logging
import os
from collections import defaultdict
from pathlib import Path

from models.user_data import UserData

logger = logging.getLogger(__name__)


class JsonStorage:
    def __init__(self, users_dir: Path) -> None:
        self._dir = users_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    def lock(self, user_id: int) -> asyncio.Lock:
        return self._locks[user_id]

    def _path(self, user_id: int) -> Path:
        return self._dir / f"{user_id}.json"

    def _read(self, user_id: int) -> UserData:
        path = self._path(user_id)
        if not path.exists():
            return UserData.new(user_id)
        try:
            return UserData.from_dict(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, KeyError, OSError):
            logger.exception("Повреждён файл %s, создаём новый профиль", path)
            path.rename(path.with_suffix(".json.broken"))
            return UserData.new(user_id)

    def _write(self, data: UserData) -> None:
        path = self._path(data.user_id)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)  # атомарная запись

    async def load(self, user_id: int) -> UserData:
        return await asyncio.to_thread(self._read, user_id)

    async def save(self, data: UserData) -> None:
        await asyncio.to_thread(self._write, data)
