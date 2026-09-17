from unittest.mock import MagicMock
import src.agents.agent_tools.tool_result_cache as tool_result_cache_module
from src.agents.agent_tools.tool_result_cache import cached_tool_call
from src.services.query_cache import QueryCache


def use_isolated_cache(monkeypatch, tmp_path):
    fake_cache = QueryCache(db_path=str(tmp_path / "test_tool_cache.sqlite3"))
    monkeypatch.setattr(tool_result_cache_module, "_cache", fake_cache)
    return fake_cache


def test_cached_tool_call_calls_fetch_on_a_miss_and_returns_its_result(monkeypatch, tmp_path):
    use_isolated_cache(monkeypatch, tmp_path)
    fetch = MagicMock(return_value={"articles": ["one"]})

    result = cached_tool_call("search_news", "nvidia", fetch)

    assert result == {"articles": ["one"]}
    fetch.assert_called_once()


def test_cached_tool_call_does_not_call_fetch_again_on_a_hit(monkeypatch, tmp_path):
    use_isolated_cache(monkeypatch, tmp_path)
    fetch = MagicMock(return_value={"articles": ["one"]})
    cached_tool_call("search_news", "nvidia", fetch)

    result = cached_tool_call("search_news", "nvidia", fetch)

    assert result == {"articles": ["one"]}
    fetch.assert_called_once()  # not called a second time


def test_cached_tool_call_normalizes_query_case_and_whitespace(monkeypatch, tmp_path):
    use_isolated_cache(monkeypatch, tmp_path)
    fetch = MagicMock(return_value={"articles": ["one"]})
    cached_tool_call("search_news", "  Nvidia  ", fetch)

    cached_tool_call("search_news", "nvidia", fetch)

    fetch.assert_called_once()  # same normalized key, second call was a hit


def test_cached_tool_call_keeps_different_tools_separate_for_the_same_query(monkeypatch, tmp_path):
    use_isolated_cache(monkeypatch, tmp_path)
    guardian_fetch = MagicMock(return_value={"articles": ["guardian"]})
    newsdata_fetch = MagicMock(return_value={"articles": ["newsdata"]})

    guardian_result = cached_tool_call("search_news", "nvidia", guardian_fetch)
    newsdata_result = cached_tool_call("search_newsdata_news", "nvidia", newsdata_fetch)

    assert guardian_result == {"articles": ["guardian"]}
    assert newsdata_result == {"articles": ["newsdata"]}


def test_cached_tool_call_does_not_cache_error_results(monkeypatch, tmp_path):
    use_isolated_cache(monkeypatch, tmp_path)
    fetch = MagicMock(return_value={"error": "boom"})
    cached_tool_call("search_news", "nvidia", fetch)

    cached_tool_call("search_news", "nvidia", fetch)

    assert fetch.call_count == 2  # errors aren't cached, so both calls hit fetch
