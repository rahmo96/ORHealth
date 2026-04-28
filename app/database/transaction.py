"""Decorators for database safety and error translation."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
import logging
from typing import Any, TypeVar

from app.core.exceptions import AppError, DatabaseAppError

LOGGER: logging.Logger = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


def db_safe_operation(func: F) -> F:
    """Wrap database-facing operations with robust error handling."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except (DatabaseAppError, AppError):
            raise
        except Exception as error:
            LOGGER.exception("Unhandled database operation error in %s.", func.__name__)
            raise DatabaseAppError("Unexpected database operation error.") from error

    return wrapper  # type: ignore[return-value]
