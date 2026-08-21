"""
Retry and fault-tolerance policies for batch execution.
"""

import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def with_retry(max_attempts: int = 3, delay_seconds: float = 1.0, backoff: float = 2.0):
    """
    Decorator for retrying unstable operations (e.g. external network requests).
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay_seconds
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {exc}. "
                        f"Retrying in {current_delay}s..."
                    )
                    if attempt < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            raise last_exception
        return wrapper
    return decorator
