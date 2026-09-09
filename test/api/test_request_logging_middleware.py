import logging
import pytest
from src.api.request_logging_middleware import RequestLoggingMiddleware


async def _run(app_events: list[dict], scope: dict) -> list[dict]:
    """Drives RequestLoggingMiddleware against a fake downstream ASGI app that just replays
    app_events via `send`, and returns everything the middleware actually sent onward."""
    sent_messages: list[dict] = []

    async def fake_app(scope, receive, send):
        for message in app_events:
            await send(message)

    middleware = RequestLoggingMiddleware(fake_app)

    async def receive():
        return {"type": "http.disconnect"}

    async def send(message):
        sent_messages.append(message)

    await middleware(scope, receive, send)
    return sent_messages


def make_scope(method: str = "GET", path: str = "/api/v1/research") -> dict:
    return {"type": "http", "method": method, "path": path}


@pytest.mark.anyio
async def test_passes_through_a_single_chunk_response_unchanged():
    events = [
        {"type": "http.response.start", "status": 200, "headers": []},
        {"type": "http.response.body", "body": b"ok", "more_body": False},
    ]

    sent = await _run(events, make_scope())

    assert sent == events


@pytest.mark.anyio
async def test_passes_through_a_multi_chunk_streaming_response_unchanged():
    events = [
        {"type": "http.response.start", "status": 200, "headers": []},
        {"type": "http.response.body", "body": b"chunk1", "more_body": True},
        {"type": "http.response.body", "body": b"chunk2", "more_body": True},
        {"type": "http.response.body", "body": b"chunk3", "more_body": False},
    ]

    sent = await _run(events, make_scope())

    assert sent == events


@pytest.mark.anyio
async def test_logs_method_path_status_and_duration_once_the_response_completes(caplog):
    events = [
        {"type": "http.response.start", "status": 200, "headers": []},
        {"type": "http.response.body", "body": b"ok", "more_body": False},
    ]

    with caplog.at_level(logging.INFO, logger="src.api.requests"):
        await _run(events, make_scope(method="POST", path="/api/v1/research"))

    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert "method=POST" in message
    assert "path=/api/v1/research" in message
    assert "status=200" in message
    assert "duration_ms=" in message


@pytest.mark.anyio
async def test_does_not_log_until_the_final_chunk_of_a_streaming_response(caplog):
    events = [
        {"type": "http.response.start", "status": 200, "headers": []},
        {"type": "http.response.body", "body": b"chunk1", "more_body": True},
        {"type": "http.response.body", "body": b"chunk2", "more_body": False},
    ]

    logged_after_each_message = []

    async def fake_app(scope, receive, send):
        for message in events:
            await send(message)
            logged_after_each_message.append(len(caplog.records))

    middleware = RequestLoggingMiddleware(fake_app)

    async def receive():
        return {"type": "http.disconnect"}

    async def send(message):
        pass

    with caplog.at_level(logging.INFO, logger="src.api.requests"):
        await middleware(make_scope(), receive, send)

    assert logged_after_each_message == [0, 0, 1]


@pytest.mark.anyio
async def test_ignores_non_http_scopes():
    sent = []

    async def fake_app(scope, receive, send):
        await send({"type": "websocket.accept"})

    middleware = RequestLoggingMiddleware(fake_app)

    async def receive():
        return {}

    async def send(message):
        sent.append(message)

    await middleware({"type": "websocket"}, receive, send)

    assert sent == [{"type": "websocket.accept"}]


@pytest.fixture
def anyio_backend():
    return "asyncio"
