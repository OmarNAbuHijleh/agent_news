from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import src.api.routes.trending as trending_module
from src.api.app import app


def make_client(monkeypatch, topics):
    fake_tracker = MagicMock()
    fake_tracker.get_top.return_value = topics
    monkeypatch.setattr(trending_module, "TrendingTopics", MagicMock(return_value=fake_tracker))
    return TestClient(app), fake_tracker


def test_trending_endpoint_returns_topics_as_json(monkeypatch):
    client, _ = make_client(monkeypatch, ["nvidia stock price", "tesla stock price"])

    response = client.get("/api/v1/trending")

    assert response.status_code == 200
    assert response.json() == {"topics": ["nvidia stock price", "tesla stock price"]}


def test_trending_endpoint_returns_empty_list_when_nothing_tracked(monkeypatch):
    client, _ = make_client(monkeypatch, [])

    response = client.get("/api/v1/trending")

    assert response.json() == {"topics": []}


def test_trending_endpoint_uses_the_configured_limit(monkeypatch):
    from config import TRENDING_TOPICS_LIMIT
    client, fake_tracker = make_client(monkeypatch, [])

    client.get("/api/v1/trending")

    fake_tracker.get_top.assert_called_once_with(TRENDING_TOPICS_LIMIT)


def test_trending_endpoint_is_not_rate_limited(monkeypatch):
    from config import RATE_LIMIT_MAX_REQUESTS
    client, _ = make_client(monkeypatch, [])

    responses = [client.get("/api/v1/trending") for _ in range(RATE_LIMIT_MAX_REQUESTS + 5)]

    assert all(r.status_code == 200 for r in responses)
