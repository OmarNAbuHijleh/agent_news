import httpx
from unittest.mock import MagicMock
import src.agents.agent_tools.news_search_tool as news_search_tool_module
from src.agents.agent_tools.news_search_tool import search_news, _fetch_guardian_news


def make_guardian_response(results: list[dict], status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"response": {"results": results}}
    response.raise_for_status = MagicMock()
    return response


def test_search_news_routes_through_the_tool_result_cache(monkeypatch):
    fake_cached_tool_call = MagicMock(return_value={"articles": []})
    monkeypatch.setattr(news_search_tool_module, "cached_tool_call", fake_cached_tool_call)
    fake_fetch = MagicMock(return_value={"articles": ["real result"]})
    monkeypatch.setattr(news_search_tool_module, "_fetch_guardian_news", fake_fetch)

    result = search_news("nvidia")

    assert result == {"articles": []}
    args, _ = fake_cached_tool_call.call_args
    assert args[0] == "search_news"
    assert args[1] == "nvidia"
    assert args[2]() == {"articles": ["real result"]}  # the passed fetch callable does the real work
    fake_fetch.assert_called_once_with("nvidia")


def test_fetch_guardian_news_returns_error_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(news_search_tool_module, "GUARDIAN_API_KEY", None)
    fake_get = MagicMock()
    monkeypatch.setattr(news_search_tool_module.httpx, "get", fake_get)

    result = _fetch_guardian_news("nvidia")

    assert result == {"error": "GUARDIAN_API_KEY is not configured"}
    fake_get.assert_not_called()


def test_fetch_guardian_news_passes_query_and_api_key_as_params(monkeypatch):
    monkeypatch.setattr(news_search_tool_module, "GUARDIAN_API_KEY", "test-key")
    fake_get = MagicMock(return_value=make_guardian_response([]))
    monkeypatch.setattr(news_search_tool_module.httpx, "get", fake_get)

    _fetch_guardian_news("nvidia earnings")

    _, kwargs = fake_get.call_args
    assert kwargs["params"]["q"] == "nvidia earnings"
    assert kwargs["params"]["api-key"] == "test-key"


def test_fetch_guardian_news_returns_headline_date_url_and_stripped_body(monkeypatch):
    monkeypatch.setattr(news_search_tool_module, "GUARDIAN_API_KEY", "test-key")
    guardian_results = [
        {
            "webTitle": "Nvidia posts record earnings",
            "webPublicationDate": "2026-09-15T10:00:00Z",
            "webUrl": "https://theguardian.com/business/nvidia-earnings",
            "fields": {"body": "<p>Nvidia reported <b>record</b> revenue.</p>"},
        }
    ]
    monkeypatch.setattr(news_search_tool_module.httpx, "get", MagicMock(return_value=make_guardian_response(guardian_results)))

    result = _fetch_guardian_news("nvidia")

    assert result == {
        "articles": [
            {
                "headline": "Nvidia posts record earnings",
                "published_at": "2026-09-15T10:00:00Z",
                "url": "https://theguardian.com/business/nvidia-earnings",
                "body": "Nvidia reported record revenue.",
            }
        ]
    }


def test_fetch_guardian_news_truncates_body_to_the_configured_max_length(monkeypatch):
    monkeypatch.setattr(news_search_tool_module, "GUARDIAN_API_KEY", "test-key")
    monkeypatch.setattr(news_search_tool_module, "NEWS_SEARCH_MAX_BODY_CHARS", 10)
    guardian_results = [{"webTitle": "t", "webPublicationDate": "d", "webUrl": "u", "fields": {"body": "0123456789ABCDEF"}}]
    monkeypatch.setattr(news_search_tool_module.httpx, "get", MagicMock(return_value=make_guardian_response(guardian_results)))

    result = _fetch_guardian_news("nvidia")

    assert result["articles"][0]["body"] == "0123456789"


def test_fetch_guardian_news_returns_error_dict_on_http_failure(monkeypatch):
    monkeypatch.setattr(news_search_tool_module, "GUARDIAN_API_KEY", "test-key")

    def raise_error(*args, **kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(news_search_tool_module.httpx, "get", MagicMock(side_effect=raise_error))

    result = _fetch_guardian_news("nvidia")

    assert "error" in result
