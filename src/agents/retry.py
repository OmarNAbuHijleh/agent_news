import time
from collections.abc import Callable
from typing import TypeVar
from google.genai.errors import ClientError

T = TypeVar("T")

_RATE_LIMIT_STATUS_CODE = 429


def call_with_retry(fn: Callable[[], T], max_retries: int = 3, base_delay_seconds: float = 2.0) -> T:
    """Calls fn, retrying with exponential backoff if the API responds with a rate-limit (429) error.
    Args:
        fn <Callable[[], T]>: A zero-argument callable wrapping the API call to perform, e.g. lambda: client.interactions.create(...)
        max_retries <int>: How many additional attempts to make after the first failure
        base_delay_seconds <float>: Delay before the first retry; doubles on each subsequent retry
    Returns:
        <T>: Whatever fn returns
    """
    attempt = 0
    while True:
        try:
            return fn()
        except ClientError as e:
            if e.code != _RATE_LIMIT_STATUS_CODE or attempt >= max_retries:
                raise
            time.sleep(base_delay_seconds * (2 ** attempt))
            attempt += 1
