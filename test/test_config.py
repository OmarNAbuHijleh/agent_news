import importlib
import config


def test_max_research_iterations_defaults_to_5(monkeypatch):
    monkeypatch.delenv("MAX_RESEARCH_ITERATIONS", raising=False)
    reloaded = importlib.reload(config)
    assert reloaded.MAX_RESEARCH_ITERATIONS == 5


def test_max_research_iterations_reads_env_override(monkeypatch):
    monkeypatch.setenv("MAX_RESEARCH_ITERATIONS", "9")
    reloaded = importlib.reload(config)
    assert reloaded.MAX_RESEARCH_ITERATIONS == 9
    importlib.reload(config)  # restore module state for other tests
