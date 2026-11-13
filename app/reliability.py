import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

def run_with_retries(operation: Callable[[], T], max_attempts: int = 3, backoff_seconds: float = 0.1) -> T:
    """Run an operation with bounded retries and exponential backoff."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return operation()
        except Exception as error:  # noqa: BLE001 - retry boundaries must capture operation failures
            last_error = error
            if attempt < max_attempts - 1:
                time.sleep(backoff_seconds * (2**attempt))
    raise last_error
