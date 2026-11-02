import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(level: str = "INFO") -> logging.Logger:
    for name in ("httpx", "httpx2", "httpcore", "openai", "vkbottle"):
        logging.getLogger(name).setLevel(logging.WARNING)
    root = logging.getLogger()
    root.setLevel(level)
    if root.handlers:
        return logging.getLogger("vk_bot")
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = RotatingFileHandler(log_dir / "bot.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    return logging.getLogger("vk_bot")
