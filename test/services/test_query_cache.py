import src.services.query_cache as query_cache_module
from src.services.query_cache import QueryCache


def make_cache(tmp_path, ttl_seconds: int = 3600) -> QueryCache:
    return QueryCache(db_path=str(tmp_path / "test_cache.sqlite3"), ttl_seconds=ttl_seconds)


def test_get_returns_none_on_miss(tmp_path):
    cache = make_cache(tmp_path)
    assert cache.get("nvidia stock price") is None


def test_set_then_get_returns_the_cached_result(tmp_path):
    cache = make_cache(tmp_path)
    cache.set("nvidia stock price", "some research result")
    assert cache.get("nvidia stock price") == "some research result"


def test_set_overwrites_an_existing_entry(tmp_path):
    cache = make_cache(tmp_path)
    cache.set("nvidia stock price", "first result")
    cache.set("nvidia stock price", "second result")
    assert cache.get("nvidia stock price") == "second result"


def test_entries_persist_across_separate_connections_to_the_same_db_file(tmp_path):
    db_path = str(tmp_path / "test_cache.sqlite3")
    QueryCache(db_path=db_path).set("nvidia stock price", "some research result")
    assert QueryCache(db_path=db_path).get("nvidia stock price") == "some research result"


def test_get_returns_none_once_the_entry_has_expired(tmp_path, monkeypatch):
    cache = make_cache(tmp_path, ttl_seconds=60)
    monkeypatch.setattr(query_cache_module.time, "time", lambda: 1000.0)
    cache.set("nvidia stock price", "some research result")

    monkeypatch.setattr(query_cache_module.time, "time", lambda: 1000.0 + 61)
    assert cache.get("nvidia stock price") is None


def test_get_still_returns_the_result_just_before_it_expires(tmp_path, monkeypatch):
    cache = make_cache(tmp_path, ttl_seconds=60)
    monkeypatch.setattr(query_cache_module.time, "time", lambda: 1000.0)
    cache.set("nvidia stock price", "some research result")

    monkeypatch.setattr(query_cache_module.time, "time", lambda: 1000.0 + 59)
    assert cache.get("nvidia stock price") == "some research result"
