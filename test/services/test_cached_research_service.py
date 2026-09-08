from unittest.mock import MagicMock
import src.services.cached_research_service as cached_service_module
from src.services.cached_research_service import CachedResearchService
from src.agents.progress_event import ProgressEvent


def make_service(monkeypatch, cached_value=None, orchestrator_events=None):
    fake_cache = MagicMock()
    fake_cache.get.return_value = cached_value
    monkeypatch.setattr(cached_service_module, "QueryCache", MagicMock(return_value=fake_cache))
    monkeypatch.setattr(cached_service_module, "normalize_query", MagicMock(return_value="normalized query"))

    fake_orchestrator = MagicMock()
    fake_orchestrator.run_streaming.return_value = iter(
        orchestrator_events if orchestrator_events is not None
        else [ProgressEvent(stage="final", content="fresh research result", done=True)]
    )
    monkeypatch.setattr(cached_service_module, "ResearchOrchestrator", MagicMock(return_value=fake_orchestrator))

    service = CachedResearchService(api_key="fake-key")
    return service, fake_cache, fake_orchestrator


# --- run (blocking) ---

def test_run_returns_cached_result_on_hit_without_running_orchestrator(monkeypatch):
    service, fake_cache, fake_orchestrator = make_service(monkeypatch, cached_value="cached result")

    result = service.run("what's nvda doing today?")

    assert result == "cached result"
    fake_orchestrator.run_streaming.assert_not_called()
    fake_cache.set.assert_not_called()


def test_run_calls_orchestrator_and_caches_result_on_miss(monkeypatch):
    service, fake_cache, fake_orchestrator = make_service(monkeypatch, cached_value=None)

    result = service.run("what's nvda doing today?")

    assert result == "fresh research result"
    fake_orchestrator.run_streaming.assert_called_once_with("what's nvda doing today?")
    fake_cache.set.assert_called_once_with("normalized query", "fresh research result")


def test_run_looks_up_cache_by_normalized_query(monkeypatch):
    service, fake_cache, _ = make_service(monkeypatch, cached_value=None)

    service.run("what's nvda doing today?")

    fake_cache.get.assert_called_once_with("normalized query")


# --- run_streaming ---

def test_run_streaming_yields_a_single_done_event_on_cache_hit(monkeypatch):
    service, _, fake_orchestrator = make_service(monkeypatch, cached_value="cached result")

    events = list(service.run_streaming("what's nvda doing today?"))

    assert events == [ProgressEvent(stage="cache_hit", content="cached result", done=True)]
    fake_orchestrator.run_streaming.assert_not_called()


def test_run_streaming_forwards_every_orchestrator_event_on_miss(monkeypatch):
    orchestrator_events = [
        ProgressEvent(stage="planning", content="Creating a research plan..."),
        ProgressEvent(stage="plan", content="1.) look it up"),
        ProgressEvent(stage="final", content="fresh research result", done=True),
    ]
    service, fake_cache, _ = make_service(monkeypatch, cached_value=None, orchestrator_events=orchestrator_events)

    events = list(service.run_streaming("what's nvda doing today?"))

    assert events == orchestrator_events
    fake_cache.set.assert_called_once_with("normalized query", "fresh research result")
