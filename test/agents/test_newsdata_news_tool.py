import httpx
from unittest.mock import MagicMock
import src.agents.agent_tools.newsdata_news_tool as newsdata_tool_module
from src.agents.agent_tools.newsdata_news_tool import search_newsdata_news


def make_newsdata_response(results: list[dict], status_code: int = 200) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = {"status": "success", "results": results}
    response.raise_for_status = MagicMock()
    return response


def test_search_newsdata_news_returns_error_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(newsdata_tool_module, "NEWSDATA_IO_API_KEY", None)
    fake_get = MagicMock()
    monkeypatch.setattr(newsdata_tool_module.httpx, "get", fake_get)

    result = search_newsdata_news("nvidia")

    assert result == {"error": "NEWSDATA_IO_API_KEY is not configured"}
    fake_get.assert_not_called()


def test_search_newsdata_news_passes_query_key_and_english_language_filter(monkeypatch):
    monkeypatch.setattr(newsdata_tool_module, "NEWSDATA_IO_API_KEY", "test-key")
    fake_get = MagicMock(return_value=make_newsdata_response([]))
    monkeypatch.setattr(newsdata_tool_module.httpx, "get", fake_get)

    search_newsdata_news("nvidia earnings")

    _, kwargs = fake_get.call_args
    assert kwargs["params"]["q"] == "nvidia earnings"
    assert kwargs["params"]["apikey"] == "test-key"
    assert kwargs["params"]["language"] == "en"


def test_search_newsdata_news_returns_headline_date_source_url_and_description(monkeypatch):
    monkeypatch.setattr(newsdata_tool_module, "NEWSDATA_IO_API_KEY", "test-key")
    newsdata_results = [
        {
            "title": "Nvidia posts record earnings",
            "pubDate": "2026-09-15 10:00:00",
            "source_name": "Some Outlet",
            "link": "https://example.com/nvidia-earnings",
            "description": "Nvidia reported record revenue.",
        }
    ]
    monkeypatch.setattr(newsdata_tool_module.httpx, "get", MagicMock(return_value=make_newsdata_response(newsdata_results)))

    result = search_newsdata_news("nvidia")

    assert result == {
        "articles": [
            {
                "headline": "Nvidia posts record earnings",
                "published_at": "2026-09-15 10:00:00",
                "source": "Some Outlet",
                "url": "https://example.com/nvidia-earnings",
                "description": "Nvidia reported record revenue.",
            }
        ]
    }


def test_search_newsdata_news_returns_error_dict_on_http_failure(monkeypatch):
    monkeypatch.setattr(newsdata_tool_module, "NEWSDATA_IO_API_KEY", "test-key")

    def raise_error(*args, **kwargs):
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(newsdata_tool_module.httpx, "get", MagicMock(side_effect=raise_error))

    result = search_newsdata_news("nvidia")

    assert "error" in result
