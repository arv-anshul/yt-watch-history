import ast
import asyncio
import functools
from typing import Any

from fastapi import HTTPException
from pymongo.errors import ServerSelectionTimeoutError

from api._logger import get_logger

logger = get_logger(__name__)


class _APIExceptionResponder:
    def __init__(self) -> None:
        self.status_code = 400  # 400: Bad Request
        self.content = None

    def update(self, status_code: int, content: Any = None) -> None:
        """Update the status code and add content for exception."""
        self.status_code = status_code
        self.content = content

    def reset(self) -> None:
        """Reset the class variables to its default values."""
        self.status_code = 400
        self.content = None

    def handel_exception(self, __e: Exception, /):
        """Handles an exception and raises as `HTTPException`."""
        logger.error(f"{type(__e).__name__!r}: {__e}")
        logger.exception(__e)

        if isinstance(__e, HTTPException):
            raise
        elif isinstance(__e, ServerSelectionTimeoutError):
            raise HTTPException(
                403,
                {
                    "message": "Failed to establish connection with database.",
                    "help": "Contact to admin to solve this issue.",
                },
            )

        try:
            message = ast.literal_eval(str(__e))
        except (ValueError, SyntaxError):
            message = str(__e)

        raise HTTPException(
            status_code=self.status_code,
            detail=(
                self.content
                if self.content
                else {"message": message, "errorType": type(__e).__name__}
            ),
        )

    def __call__(self, func):
        @functools.wraps(func)
        async def handel_exception_wrapper(*args, **kwargs):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                self.handel_exception(e)
            finally:
                self.reset()

        return handel_exception_wrapper


APIExceptionResponder = _APIExceptionResponder()
