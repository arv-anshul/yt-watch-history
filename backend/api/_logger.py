import functools
import logging
import os
import warnings
from datetime import datetime
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL")
STREAM_LOGS = os.getenv("STREAM_LOGS")


@functools.lru_cache(maxsize=1)
def __get_log_level() -> int:
    global LOG_LEVEL
    if LOG_LEVEL is None:
        LOG_LEVEL = "INFO"
        warnings.warn(
            f"Set 'LOG_LEVEL' env. Setting default to {LOG_LEVEL!r}",
            category=UserWarning,
            stacklevel=2,
        )
    if LOG_LEVEL in logging._nameToLevel:
        return getattr(logging, LOG_LEVEL)
    raise ValueError(f"{LOG_LEVEL!r} is not valid log level.")


def load_logging():
    if STREAM_LOGS is None:
        warnings.warn(
            "Set 'STREAM_LOGS' env. To show all logging in console too.",
            category=UserWarning,
            stacklevel=2,
        )

    log_file_path = Path(f"logs/api/{datetime.now():%d%m%y-%H%M}.log")
    if not log_file_path.exists():
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        format="[%(asctime)s]:%(levelname)s:%(lineno)s:%(name)s> %(message)s",
        level=__get_log_level(),
        handlers=[
            logging.StreamHandler()
            if any(i == STREAM_LOGS for i in (True, "true", "True"))
            else logging.NullHandler(),
            logging.FileHandler(log_file_path),
        ],
    )
