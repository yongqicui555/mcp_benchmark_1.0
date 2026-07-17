"""
Retry with exponential backoff and jitter.

Used for FAISS/embedding operations that can transiently fail.
Integrated with circuit breaker — retries happen inside the circuit.
"""

from __future__ import annotations

import random
import time
from functools import wraps
from typing import Any, Callable, Type

import structlog

logger = structlog.get_logger()

# Errors considered transient (worth retrying)
RETRYABLE_ERRORS = (
    TimeoutError,
    ConnectionError,
    OSError,
    RuntimeError,   # catch FAISS/embedding transient failures
)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 5.0,
    backoff_factor: float = 2.0,
    retryable: tuple[Type[BaseException], ...] = RETRYABLE_ERRORS,
):
    """Decorator: retry a function with exponential backoff + jitter.

    Usage:
        @retry_with_backoff(max_retries=3, base_delay=0.1)
        def _embed_texts(texts):
            ...

    Args:
        max_retries: Max retry attempts (total attempts = 1 + max_retries)
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        backoff_factor: Multiplier per retry
        retryable: Exception types considered transient
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retryable as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = min(base_delay * (backoff_factor ** attempt), max_delay)
                        jitter = random.uniform(0, delay * 0.5)
                        total_delay = delay + jitter
                        logger.debug(
                            "retry_attempt",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            delay=round(total_delay, 3),
                            error=str(e)[:100],
                        )
                        time.sleep(total_delay)
            # All retry attempts exhausted
            logger.warning(
                "retry_exhausted",
                function=func.__name__,
                attempts=max_retries + 1,
                error=str(last_exception)[:100] if last_exception else "unknown",
            )
            raise last_exception  # type: ignore[misc]
        return wrapper
    return decorator
