from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from time import sleep
from typing import TypeVar


T = TypeVar("T")


def retry(times: int = 3, delay_seconds: float = 0.2) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            last_error: Exception | None = None
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:  # pragma: no cover - used by later providers
                    last_error = exc
                    if attempt < times - 1:
                        sleep(delay_seconds)
            assert last_error is not None
            raise last_error

        return wrapper

    return decorator
