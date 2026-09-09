from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import src.api.routes.ask as ask_module
from src.api.app import app


def make_client(monkeypatch, answer="the answer"):
    fake_agent = MagicMock(return_value=answer)
    monkeypatch.setattr(ask_module, "investigation_qa_agent", fake_agent)
    return TestClient(app), fake_agent


def test_ask_endpoint_returns_the_answer_as_json(monkeypatch):
    client, _ = make_client(monkeypatch, answer="the margin is high because of pricing power")

    response = client.post("/api/v1/ask", json={"context": "evidence text", "question": "why?"})

    assert response.status_code == 200
    assert response.json() == {"answer": "the margin is high because of pricing power"}


def test_ask_endpoint_passes_context_and_question_through(monkeypatch):
    client, fake_agent = make_client(monkeypatch)

    client.post("/api/v1/ask", json={"context": "evidence text", "question": "why?"})

    args, _ = fake_agent.call_args
    assert args[1] == "evidence text"
    assert args[2] == "why?"


def test_ask_endpoint_rejects_empty_context(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post("/api/v1/ask", json={"context": "", "question": "why?"})

    assert response.status_code == 422


def test_ask_endpoint_rejects_empty_question(monkeypatch):
    client, _ = make_client(monkeypatch)

    response = client.post("/api/v1/ask", json={"context": "evidence text", "question": ""})

    assert response.status_code == 422


def test_ask_endpoint_returns_429_once_rate_limit_exceeded(monkeypatch):
    from config import RATE_LIMIT_MAX_REQUESTS
    client, _ = make_client(monkeypatch)

    responses = [
        client.post("/api/v1/ask", json={"context": "evidence text", "question": "why?"})
        for _ in range(RATE_LIMIT_MAX_REQUESTS + 1)
    ]

    assert [r.status_code for r in responses[:RATE_LIMIT_MAX_REQUESTS]] == [200] * RATE_LIMIT_MAX_REQUESTS
    assert responses[-1].status_code == 429
