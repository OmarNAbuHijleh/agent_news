"""Shared fixtures for faking the google-genai SDK's interaction/usage/step objects, so
agent code can be tested without making real (billed) API calls.
"""
from dataclasses import dataclass, field
from typing import Any, Optional
import pytest


@dataclass
class FakeUsage:
    total_input_tokens: int = 10
    total_output_tokens: int = 10
    total_tool_use_tokens: int = 0
    total_tokens: int = 20


@dataclass
class FakeStep:
    type: str
    name: str = ""
    id: str = ""
    arguments: dict = field(default_factory=dict)


@dataclass
class FakeInteraction:
    output_text: Optional[str] = ""
    id: str = "fake-interaction-id"
    steps: list = field(default_factory=list)
    usage: Any = field(default_factory=FakeUsage)


@pytest.fixture
def make_interaction():
    """Factory for a fake google-genai Interaction: make_interaction(output_text=..., steps=..., usage=...)."""
    def _make(output_text: Optional[str] = "", steps: Optional[list] = None, usage: Any = "unset", id: str = "fake-interaction-id"):
        return FakeInteraction(
            output_text=output_text,
            steps=steps or [],
            usage=FakeUsage() if usage == "unset" else usage,
            id=id,
        )
    return _make


@pytest.fixture
def make_function_call_step():
    """Factory for a fake function_call step, as would appear on interaction.steps."""
    def _make(name: str = "google_search", id: str = "call-1", arguments: Optional[dict] = None):
        return FakeStep(type="function_call", name=name, id=id, arguments=arguments or {})
    return _make


@pytest.fixture
def make_rate_limit_error():
    """Factory for a real google.genai._gaos.lib.compat_errors.RateLimitError, bypassing its
    httpx.Response-requiring __init__ since tests only need the status_code attribute checked
    by call_with_retry."""
    def _make(status_code: int = 429):
        from google.genai._gaos.lib.compat_errors import RateLimitError
        err = RateLimitError.__new__(RateLimitError)
        err.status_code = status_code
        return err
    return _make


@pytest.fixture
def make_client_error():
    """Factory for a real google.genai.errors.ClientError, bypassing its response-requiring
    __init__ since tests only need the code attribute checked by call_with_retry."""
    def _make(code: int = 429):
        from google.genai.errors import ClientError
        err = ClientError.__new__(ClientError)
        err.code = code
        return err
    return _make
