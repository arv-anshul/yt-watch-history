import functools
import logging
from datetime import datetime as dt
from pathlib import Path


def __configure_logger(logger: logging.Logger, fp: Path):
    logger.setLevel(logging.INFO)
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
