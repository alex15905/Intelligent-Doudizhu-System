import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from . import __init__ as _  # 只是确保包加载
from app.config import LOG_DIR

LOG_FILE = LOG_DIR / "app.log"


def get_logger(name: str = "doudizhu") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)

    # 文件输出（滚动）
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_fmt = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logger.info("Logger initialized. Log file: %s", LOG_FILE)
    return logger


# 默认 logger
logger = get_logger()
