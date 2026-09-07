from unittest.mock import MagicMock
import pytest
from src.agents.retry import call_with_retry, RateLimitError, ClientError


def test_call_with_retry_returns_result_on_first_success(make_interaction):
    interaction = make_interaction(output_text="hello")
    fn = MagicMock(return_value=interaction)

    result = call_with_retry(fn, stage="test")

    assert result is interaction
    fn.assert_called_once()


def test_call_with_retry_handles_missing_usage_without_crashing(make_interaction):
    interaction = make_interaction(output_text="hello", usage=None)
    fn = MagicMock(return_value=interaction)

    result = call_with_retry(fn, stage="test")

    assert result is interaction


def test_call_with_retry_retries_on_rate_limit_error_then_succeeds(make_interaction, make_rate_limit_error, monkeypatch):
    monkeypatch.setattr("src.agents.retry.time.sleep", lambda seconds: None)
    interaction = make_interaction(output_text="ok")
    fn = MagicMock(side_effect=[make_rate_limit_error(), make_rate_limit_error(), interaction])

    result = call_with_retry(fn, stage="test", max_retries=3, base_delay_seconds=0.01)

    assert result is interaction
    assert fn.call_count == 3


def test_call_with_retry_retries_on_legacy_client_error_429_too(make_interaction, make_client_error, monkeypatch):
    """Regression test: client.interactions actually raises RateLimitError (see
    make_rate_limit_error), not ClientError, but call_with_retry should still handle a
    ClientError(code=429) in case some other call path uses the legacy client surface."""
    monkeypatch.setattr("src.agents.retry.time.sleep", lambda seconds: None)
    interaction = make_interaction(output_text="ok")
    fn = MagicMock(side_effect=[make_client_error(code=429), interaction])

    result = call_with_retry(fn, stage="test", max_retries=1, base_delay_seconds=0.01)

    assert result is interaction
    assert fn.call_count == 2


def test_call_with_retry_raises_after_exhausting_retries(make_rate_limit_error, monkeypatch):
    monkeypatch.setattr("src.agents.retry.time.sleep", lambda seconds: None)
    fn = MagicMock(side_effect=make_rate_limit_error())

    with pytest.raises(RateLimitError):
        call_with_retry(fn, stage="test", max_retries=2, base_delay_seconds=0.01)

    assert fn.call_count == 3  # initial attempt + 2 retries


def test_call_with_retry_does_not_retry_non_rate_limit_client_errors(make_client_error, monkeypatch):
    monkeypatch.setattr("src.agents.retry.time.sleep", lambda seconds: None)
    fn = MagicMock(side_effect=make_client_error(code=400))

    with pytest.raises(ClientError):
        call_with_retry(fn, stage="test")

    fn.assert_called_once()
