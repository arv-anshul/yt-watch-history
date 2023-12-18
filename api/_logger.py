import functools
import logging
import os
from datetime import datetime as dt
from pathlib import Path

import dotenv


@functools.cache
def __get_log_level() -> int:
    dotenv.load_dotenv()  # Load .env file explicitly once
    level = os.getenv("API_LOG_LEVEL")
    if level is None:
        raise ValueError("Provide 'API_LOG_LEVEL' variable in '.env' file.")
    if level in logging._nameToLevel:
        return getattr(logging, level)
    raise ValueError(f"{level!r} is not valid log level.")


def __configure_logger(logger: logging.Logger, fp: Path):
    logger.setLevel(__get_log_level())
    fp.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(fp)
    formatter = logging.Formatter(
        "[%(asctime)s]:%(levelname)s:%(name)s:%(lineno)d - %(message)s"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


@functools.lru_cache
def get_logger(logger_name: str) -> logging.Logger:
    log_file_path = Path(f"logs/api/{dt.now():%d%m%y-%H}.log")
    logger = logging.getLogger(logger_name)
    __configure_logger(logger, log_file_path)
    return logger
