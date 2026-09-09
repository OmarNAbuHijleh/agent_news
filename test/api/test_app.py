import json
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import src.api.routes.research as research_module
from src.api.app import app
from src.agents.progress_event import ProgressEvent


def make_client(monkeypatch, events):
    fake_service = MagicMock()
    # side_effect (not return_value) so each call gets a fresh iterator - matters for the
    # rate-limit test below, which calls the endpoint more than once.
    fake_service.run_streaming.side_effect = lambda query: iter(events)
    monkeypatch.setattr(research_module, "CachedResearchService", MagicMock(return_value=fake_service))
    return TestClient(app), fake_service


def parse_sse_events(body: str) -> list[dict]:
    return [json.loads(chunk[len("data: "):]) for chunk in body.split("\n\n") if chunk.startswith("data: ")]


def test_research_endpoint_streams_every_progress_event_as_sse(monkeypatch):
    events = [
        ProgressEvent(stage="planning", content="Creating a research plan..."),
        ProgressEvent(stage="plan", content="1.) look it up"),
        ProgressEvent(stage="final", content="the report", done=True),
    ]
    client, fake_service = make_client(monkeypatch, events)

    response = client.post("/api/v1/research", json={"query": "nvidia stock price"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    parsed = parse_sse_events(response.text)
    assert parsed == [
        {"stage": "planning", "content": "Creating a research plan...", "done": False},
        {"stage": "plan", "content": "1.) look it up", "done": False},
        {"stage": "final", "content": "the report", "done": True},
    ]


def test_research_endpoint_passes_query_through_to_the_service(monkeypatch):
    client, fake_service = make_client(monkeypatch, [ProgressEvent(stage="final", content="ok", done=True)])

    client.post("/api/v1/research", json={"query": "nvidia stock price"})

    fake_service.run_streaming.assert_called_once_with("nvidia stock price")


def test_research_endpoint_rejects_missing_query(monkeypatch):
    client, _ = make_client(monkeypatch, [])

    response = client.post("/api/v1/research", json={})

    assert response.status_code == 422


def test_index_page_is_served_at_root(monkeypatch):
    client, _ = make_client(monkeypatch, [])

    response = client.get("/")

    assert response.status_code == 200
    assert "Agentic News Research" in response.text


def test_research_endpoint_returns_429_once_rate_limit_exceeded(monkeypatch):
    from config import RATE_LIMIT_MAX_REQUESTS
    client, _ = make_client(monkeypatch, [ProgressEvent(stage="final", content="ok", done=True)])

    responses = [client.post("/api/v1/research", json={"query": "q"}) for _ in range(RATE_LIMIT_MAX_REQUESTS + 1)]

    assert [r.status_code for r in responses[:RATE_LIMIT_MAX_REQUESTS]] == [200] * RATE_LIMIT_MAX_REQUESTS
    assert responses[-1].status_code == 429
