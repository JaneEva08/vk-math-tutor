"""Точка входа VK AI-бота (LongPoll)."""

import logging

from bot.bot import create_bot
from config.settings import get_settings, ROOT_DIR
from utils.logger import setup_logger
from utils.instance_lock import single_instance


def main() -> None:
    settings = get_settings()
    setup_logger(settings.log_level)
    logging.getLogger("vk_bot").info("Запуск VK AI-бота...")
    with single_instance(ROOT_DIR / "bot.lock"):
        bot = create_bot(settings)
        bot.run()


if __name__ == "__main__":
    main()
