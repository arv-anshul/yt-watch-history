import functools
import logging
import os
from datetime import datetime
from pathlib import Path


@functools.cache
def __get_log_level() -> int:
    level = os.getenv("API_LOG_LEVEL")
    if level is None:
        raise ValueError("Provide 'API_LOG_LEVEL' variable in '.env' file.")
    if level in logging._nameToLevel:
        return getattr(logging, level)
    raise ValueError(f"{level!r} is not valid log level.")


def load_logging():
    logs_fp = Path(f"logs/api/{datetime.now():%d%m%y-%H%M}.log")
    if not logs_fp.exists():
        logs_fp.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=logs_fp,
        format="[%(asctime)s]:%(levelname)s:%(message)s",
        level=__get_log_level(),
    )
