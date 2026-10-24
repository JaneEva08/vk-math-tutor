"""Точка входа VK AI-бота (LongPoll)."""

import logging

from bot.bot import create_bot
from config.settings import get_settings
from utils.logger import setup_logger


def main() -> None:
    settings = get_settings()
    setup_logger(settings.log_level)
    logging.getLogger("vk_bot").info("Запуск VK AI-бота...")
    bot = create_bot(settings)
    bot.run_forever()  # VKBottle сам создаёт и крутит event loop


if __name__ == "__main__":
    main()
