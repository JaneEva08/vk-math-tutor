"""Сборка бота: зависимости, роутинг, LongPoll."""

import logging

from vkbottle.bot import Bot

from bot.handlers import BotHandlers
from config.settings import Settings
from services.ai_service import AIService
from services.dialog_service import DialogService
from storage.json_storage import JsonStorage
from storage.memory_manager import MemoryManager

logger = logging.getLogger(__name__)


def create_bot(settings: Settings) -> Bot:
    settings.validate()
    handlers = BotHandlers(
        settings=settings,
        storage=JsonStorage(settings.users_dir),
        dialogs=DialogService(),
        memory=MemoryManager(settings.max_history_messages),
        ai=AIService.from_settings(settings),
    )
    bot = Bot(token=settings.vk_token)
    bot.labeler.message()(handlers.on_message)
    logger.info("Бот инициализирован, модель=%s", settings.gemini_model)
    return bot
