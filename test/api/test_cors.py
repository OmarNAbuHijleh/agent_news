import importlib
from fastapi.testclient import TestClient
import config
import src.api.app as app_module


def _build_app_with_origins(monkeypatch, origins_csv):
    """CORS_ALLOWED_ORIGINS is read once at import time and baked into the CORSMiddleware
    instance, so exercising a different value means reloading config and the app module - same
    pattern as test_config.py's env-var tests."""
    if origins_csv is None:
        monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    else:
        monkeypatch.setenv("CORS_ALLOWED_ORIGINS", origins_csv)
    importlib.reload(config)
    reloaded = importlib.reload(app_module)
    return reloaded.app


def _restore_default_app(monkeypatch):
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)
    importlib.reload(config)
    importlib.reload(app_module)


def test_cors_headers_absent_by_default(monkeypatch):
    app = _build_app_with_origins(monkeypatch, None)
    client = TestClient(app)

    response = client.get("/", headers={"Origin": "https://example.com"})

    assert "access-control-allow-origin" not in response.headers
    _restore_default_app(monkeypatch)


def test_cors_allows_a_configured_origin(monkeypatch):
    app = _build_app_with_origins(monkeypatch, "https://my-frontend.com")
    client = TestClient(app)

    response = client.get("/", headers={"Origin": "https://my-frontend.com"})

    assert response.headers["access-control-allow-origin"] == "https://my-frontend.com"
    _restore_default_app(monkeypatch)


def test_cors_rejects_an_unconfigured_origin(monkeypatch):
    app = _build_app_with_origins(monkeypatch, "https://my-frontend.com")
    client = TestClient(app)

    response = client.get("/", headers={"Origin": "https://not-allowed.com"})

    assert "access-control-allow-origin" not in response.headers
    _restore_default_app(monkeypatch)


def test_cors_preflight_allows_post_and_content_type_for_configured_origin(monkeypatch):
    app = _build_app_with_origins(monkeypatch, "https://my-frontend.com")
    client = TestClient(app)

    response = client.options(
        "/api/v1/research",
        headers={
            "Origin": "https://my-frontend.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://my-frontend.com"
    _restore_default_app(monkeypatch)


def test_cors_allows_multiple_comma_separated_origins(monkeypatch):
    app = _build_app_with_origins(monkeypatch, "https://a.com,https://b.com")
    client = TestClient(app)

    response_a = client.get("/", headers={"Origin": "https://a.com"})
    response_b = client.get("/", headers={"Origin": "https://b.com"})

    assert response_a.headers["access-control-allow-origin"] == "https://a.com"
    assert response_b.headers["access-control-allow-origin"] == "https://b.com"
    _restore_default_app(monkeypatch)
