import logging
import time
from collections.abc import Callable
from typing import TypeVar
# `client.interactions` (GeminiNextGenInteractions) raises through the _gaos compat error
# hierarchy, not the legacy google.genai.errors hierarchy used by older client surfaces
# (e.g. client.models.*). Confirmed against the installed SDK: google.genai.errors.ClientError
# is never raised here, only google.genai._gaos.lib.compat_errors.RateLimitError (status_code=429).
# This is a private import path and may break on a google-genai upgrade; if so, re-check
# `client.interactions.__class__.__module__` and the exception type in the new version.
from google.genai._gaos.lib.compat_errors import RateLimitError
from google.genai.errors import ClientError

logger = logging.getLogger(__name__)

T = TypeVar("T")

_RATE_LIMIT_STATUS_CODE = 429


def call_with_retry(fn: Callable[[], T], stage: str, max_retries: int = 3, base_delay_seconds: float = 2.0) -> T:
    """Calls fn, retrying with exponential backoff if the API responds with a rate-limit (429) error.
    Logs token usage for the call on success, so per-stage cost can be tracked.
    Args:
        fn <Callable[[], T]>: A zero-argument callable wrapping the API call to perform, e.g. lambda: client.interactions.create(...)
        stage <str>: Label identifying which pipeline stage/call this is, used in log output
        max_retries <int>: How many additional attempts to make after the first failure
        base_delay_seconds <float>: Delay before the first retry; doubles on each subsequent retry
    Returns:
        <T>: Whatever fn returns
    """
    attempt = 0
    while True:
        try:
            result = fn()
            _log_usage(stage, result)
            return result
        except (RateLimitError, ClientError) as e:
            status_code = getattr(e, "status_code", None) or getattr(e, "code", None)
            if status_code != _RATE_LIMIT_STATUS_CODE or attempt >= max_retries:
                raise
            delay = base_delay_seconds * (2 ** attempt)
            logger.warning("%s: rate limited (attempt %d/%d), retrying in %.1fs", stage, attempt + 1, max_retries, delay)
            time.sleep(delay)
            attempt += 1


def _log_usage(stage: str, interaction) -> None:
    usage = getattr(interaction, "usage", None)
    if usage is None:
        return
    logger.info(
        "%s usage: input=%s output=%s tool_use=%s total=%s",
        stage,
        usage.total_input_tokens,
        usage.total_output_tokens,
        usage.total_tool_use_tokens,
        usage.total_tokens,
    )
