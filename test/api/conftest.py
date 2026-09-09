import pytest
from src.api.rate_limiter import limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """TestClient always reports the same client host ('testclient'), and the rate limiter's
    in-memory storage is a module-level singleton - without this, request counts would
    accumulate across unrelated tests instead of resetting per test."""
    limiter.reset()
    yield
    limiter.reset()
