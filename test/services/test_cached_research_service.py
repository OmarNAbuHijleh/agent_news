import json
from unittest.mock import MagicMock
import src.services.cached_research_service as cached_service_module
from src.services.cached_research_service import CachedResearchService
from src.agents.progress_event import ProgressEvent


def make_service(monkeypatch, cached_events=None, orchestrator_events=None):
    fake_cache = MagicMock()
    fake_cache.get.return_value = (
        json.dumps([{"stage": e.stage, "content": e.content, "done": e.done} for e in cached_events])
        if cached_events is not None else None
    )
    monkeypatch.setattr(cached_service_module, "QueryCache", MagicMock(return_value=fake_cache))
    monkeypatch.setattr(cached_service_module, "normalize_query", MagicMock(return_value="normalized query"))

    fake_trending = MagicMock()
    monkeypatch.setattr(cached_service_module, "TrendingTopics", MagicMock(return_value=fake_trending))

    fake_orchestrator = MagicMock()
    fake_orchestrator.run_streaming.return_value = iter(
        orchestrator_events if orchestrator_events is not None
        else [ProgressEvent(stage="final", content="fresh research result", done=True)]
    )
    monkeypatch.setattr(cached_service_module, "ResearchOrchestrator", MagicMock(return_value=fake_orchestrator))

    service = CachedResearchService(api_key="fake-key")
    return service, fake_cache, fake_orchestrator, fake_trending


# --- run (blocking) ---

def test_run_returns_the_final_cached_event_content_on_hit(monkeypatch):
    cached_events = [ProgressEvent(stage="plan", content="the plan"), ProgressEvent(stage="final", content="the final report", done=True)]
    service, fake_cache, fake_orchestrator, _ = make_service(monkeypatch, cached_events=cached_events)

    result = service.run("what's nvda doing today?")

    assert result == "the final report"
    fake_orchestrator.run_streaming.assert_not_called()
    fake_cache.set.assert_not_called()


def test_run_calls_orchestrator_and_caches_result_on_miss(monkeypatch):
    service, fake_cache, fake_orchestrator, _ = make_service(monkeypatch, cached_events=None)

    result = service.run("what's nvda doing today?")

    assert result == "fresh research result"
    fake_orchestrator.run_streaming.assert_called_once_with("what's nvda doing today?")
    fake_cache.set.assert_called_once()


def test_run_looks_up_cache_by_normalized_query(monkeypatch):
    service, fake_cache, _, _ = make_service(monkeypatch, cached_events=None)

    service.run("what's nvda doing today?")

    fake_cache.get.assert_called_once_with("normalized query")


# --- run_streaming: cache hit replays the full evidence trail ---

def test_run_streaming_on_hit_yields_a_notice_then_replays_every_cached_event(monkeypatch):
    cached_events = [
        ProgressEvent(stage="plan", content="1.) look it up"),
        ProgressEvent(stage="research_result", content="found some things"),
        ProgressEvent(stage="fact_check_result", content="checks out"),
        ProgressEvent(stage="final", content="the final report", done=True),
    ]
    service, _, fake_orchestrator, _ = make_service(monkeypatch, cached_events=cached_events)

    events = list(service.run_streaming("what's nvda doing today?"))

    assert events[0].stage == "cache_hit_notice"
    assert events[0].done is False
    assert events[1:] == cached_events
    fake_orchestrator.run_streaming.assert_not_called()


def test_run_streaming_on_hit_gracefully_treats_unparseable_cache_entries_as_a_miss(monkeypatch):
    service, fake_cache, fake_orchestrator, _ = make_service(monkeypatch, cached_events=None)
    fake_cache.get.return_value = "not valid json"

    events = list(service.run_streaming("what's nvda doing today?"))

    assert events == [ProgressEvent(stage="final", content="fresh research result", done=True)]
    fake_orchestrator.run_streaming.assert_called_once()


# --- run_streaming: cache miss forwards live progress and caches only the evidence ---

def test_run_streaming_forwards_every_orchestrator_event_live_on_miss(monkeypatch):
    orchestrator_events = [
        ProgressEvent(stage="planning", content="Creating a research plan..."),
        ProgressEvent(stage="plan", content="1.) look it up"),
        ProgressEvent(stage="final", content="fresh research result", done=True),
    ]
    service, fake_cache, _, _ = make_service(monkeypatch, cached_events=None, orchestrator_events=orchestrator_events)

    events = list(service.run_streaming("what's nvda doing today?"))

    assert events == orchestrator_events


def test_run_streaming_caches_only_the_evidence_events_not_transient_status_events(monkeypatch):
    orchestrator_events = [
        ProgressEvent(stage="planning", content="Creating a research plan..."),
        ProgressEvent(stage="plan", content="1.) look it up"),
        ProgressEvent(stage="researching", content="Researching (iteration 1)..."),
        ProgressEvent(stage="research_result", content="found some things"),
        ProgressEvent(stage="fact_checking", content="Fact-checking the research..."),
        ProgressEvent(stage="fact_check_result", content="checks out"),
        ProgressEvent(stage="synthesizing", content="Synthesizing the final report..."),
        ProgressEvent(stage="final", content="fresh research result", done=True),
    ]
    service, fake_cache, _, _ = make_service(monkeypatch, cached_events=None, orchestrator_events=orchestrator_events)

    list(service.run_streaming("what's nvda doing today?"))

    args, _ = fake_cache.set.call_args
    normalized_query, cached_json = args
    assert normalized_query == "normalized query"
    assert json.loads(cached_json) == [
        {"stage": "plan", "content": "1.) look it up", "done": False},
        {"stage": "research_result", "content": "found some things", "done": False},
        {"stage": "fact_check_result", "content": "checks out", "done": False},
        {"stage": "final", "content": "fresh research result", "done": True},
    ]


# --- trending ---

def test_run_streaming_records_query_as_trending_on_hit(monkeypatch):
    cached_events = [ProgressEvent(stage="final", content="cached result", done=True)]
    service, _, _, fake_trending = make_service(monkeypatch, cached_events=cached_events)

    list(service.run_streaming("what's nvda doing today?"))

    fake_trending.record_query.assert_called_once_with("normalized query")


def test_run_streaming_records_query_as_trending_on_miss(monkeypatch):
    service, _, _, fake_trending = make_service(monkeypatch, cached_events=None)

    list(service.run_streaming("what's nvda doing today?"))

    fake_trending.record_query.assert_called_once_with("normalized query")
