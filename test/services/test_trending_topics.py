import src.services.trending_topics as trending_topics_module
from src.services.trending_topics import TrendingTopics


def make_tracker(tmp_path) -> TrendingTopics:
    return TrendingTopics(db_path=str(tmp_path / "test_trending.sqlite3"))


def test_get_top_returns_empty_list_when_nothing_recorded(tmp_path):
    tracker = make_tracker(tmp_path)
    assert tracker.get_top() == []


def test_record_query_makes_it_appear_in_get_top(tmp_path):
    tracker = make_tracker(tmp_path)
    tracker.record_query("nvidia stock price")
    assert tracker.get_top() == ["nvidia stock price"]


def test_get_top_orders_by_ask_count_descending(tmp_path):
    tracker = make_tracker(tmp_path)
    tracker.record_query("nvidia stock price")
    tracker.record_query("tesla stock price")
    tracker.record_query("tesla stock price")
    tracker.record_query("tesla stock price")

    assert tracker.get_top() == ["tesla stock price", "nvidia stock price"]


def test_get_top_respects_limit(tmp_path):
    tracker = make_tracker(tmp_path)
    for topic in ["a", "b", "c", "d"]:
        tracker.record_query(topic)

    assert len(tracker.get_top(limit=2)) == 2


def test_get_top_breaks_ties_by_most_recently_asked(tmp_path, monkeypatch):
    tracker = make_tracker(tmp_path)
    monkeypatch.setattr(trending_topics_module.time, "time", lambda: 1000.0)
    tracker.record_query("older topic")
    monkeypatch.setattr(trending_topics_module.time, "time", lambda: 2000.0)
    tracker.record_query("newer topic")

    assert tracker.get_top() == ["newer topic", "older topic"]


def test_counts_persist_across_separate_connections_to_the_same_db_file(tmp_path):
    db_path = str(tmp_path / "test_trending.sqlite3")
    TrendingTopics(db_path=db_path).record_query("nvidia stock price")
    TrendingTopics(db_path=db_path).record_query("nvidia stock price")

    assert TrendingTopics(db_path=db_path).get_top() == ["nvidia stock price"]
