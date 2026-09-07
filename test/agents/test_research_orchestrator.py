from unittest.mock import MagicMock
import pytest
import src.agents.research_orchestrator as orchestrator_module
from src.agents.research_orchestrator import ResearchOrchestrator
from src.agents.agent_type_enum import AgentType
from src.agents.research_step import ResearchStep


@pytest.fixture
def orchestrator():
    return ResearchOrchestrator(api_key="fake-key")


# --- create_plan ---

def test_create_plan_without_history_uses_query_as_input(orchestrator, make_interaction):
    orchestrator._client.interactions.create = MagicMock(return_value=make_interaction(output_text="1.) step one"))

    plan = orchestrator.create_plan("what is nvidia stock price")

    assert plan == "1.) step one"
    _, kwargs = orchestrator._client.interactions.create.call_args
    assert kwargs["input"] == "what is nvidia stock price"


def test_create_plan_with_history_includes_prior_research(orchestrator, make_interaction):
    orchestrator._client.interactions.create = MagicMock(return_value=make_interaction(output_text="revised plan"))
    history = [ResearchStep(AgentType.RESEARCHER, "earlier findings")]

    orchestrator.create_plan("query", research_so_far=history)

    _, kwargs = orchestrator._client.interactions.create.call_args
    assert "query" in kwargs["input"]
    assert "earlier findings" in kwargs["input"]


def test_create_plan_returns_empty_string_for_falsy_output(orchestrator, make_interaction):
    orchestrator._client.interactions.create = MagicMock(return_value=make_interaction(output_text=None))

    assert orchestrator.create_plan("query") == ""


# --- results_acceptable ---

def test_results_acceptable_satisfied_ends_research(orchestrator, make_interaction):
    orchestrator._client.interactions.create = MagicMock(return_value=make_interaction(output_text="SATISFIED"))

    not_completed, plan = orchestrator.results_acceptable("results", "fact check", "query", [])

    assert not_completed is False
    assert plan == ""


def test_results_acceptable_unsatisfied_replans_with_full_history(orchestrator, make_interaction, monkeypatch):
    """Regression test for the bug fixed in 0.1.5: research_so_far must be threaded through to
    create_plan on re-plan, not dropped."""
    orchestrator._client.interactions.create = MagicMock(return_value=make_interaction(output_text="UNSATISFIED"))
    captured = {}

    def fake_create_plan(user_input_query, research_so_far=None):
        captured["user_input_query"] = user_input_query
        captured["research_so_far"] = research_so_far
        return "revised plan"

    monkeypatch.setattr(orchestrator, "create_plan", fake_create_plan)
    history = [ResearchStep(AgentType.RESEARCHER, "earlier findings")]

    not_completed, plan = orchestrator.results_acceptable("results", "fact check", "query", history)

    assert not_completed is True
    assert plan == "revised plan"
    assert captured["research_so_far"] is history
    assert captured["user_input_query"] == "query"


def test_results_acceptable_raises_on_unexpected_output(orchestrator, make_interaction):
    orchestrator._client.interactions.create = MagicMock(return_value=make_interaction(output_text="MAYBE"))

    with pytest.raises(Exception):
        orchestrator.results_acceptable("results", "fact check", "query", [])


# --- run ---

def test_run_completes_after_one_satisfied_iteration(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator_module, "research_agent", MagicMock(return_value="research results"))
    monkeypatch.setattr(orchestrator_module, "fact_checking_agent", MagicMock(return_value="fact check results"))
    monkeypatch.setattr(orchestrator_module, "synthesis_agent", MagicMock(return_value="final summary"))
    monkeypatch.setattr(orchestrator, "create_plan", MagicMock(return_value="a plan"))
    monkeypatch.setattr(orchestrator, "results_acceptable", MagicMock(return_value=(False, "")))

    result = orchestrator.run("what is nvidia stock price")

    assert result == "final summary"
    expected_history = [
        ResearchStep(AgentType.RESEARCH_PLANNER, "a plan"),
        ResearchStep(AgentType.RESEARCHER, "research results"),
        ResearchStep(AgentType.FACT_CHECKING, "fact check results"),
    ]
    orchestrator_module.synthesis_agent.assert_called_once_with(orchestrator._client, expected_history)


def test_run_continues_looping_until_satisfied(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator_module, "research_agent", MagicMock(return_value="research results"))
    monkeypatch.setattr(orchestrator_module, "fact_checking_agent", MagicMock(return_value="fact check results"))
    monkeypatch.setattr(orchestrator_module, "synthesis_agent", MagicMock(return_value="final summary"))
    monkeypatch.setattr(orchestrator, "create_plan", MagicMock(return_value="a plan"))
    # unsatisfied once, then satisfied
    monkeypatch.setattr(orchestrator, "results_acceptable", MagicMock(side_effect=[(True, "revised plan"), (False, "")]))

    result = orchestrator.run("what is nvidia stock price")

    assert result == "final summary"
    assert orchestrator_module.research_agent.call_count == 2
    assert orchestrator_module.fact_checking_agent.call_count == 2


def test_run_raises_once_max_iterations_exceeded(orchestrator, monkeypatch):
    monkeypatch.setattr(orchestrator_module, "MAX_RESEARCH_ITERATIONS", 1)
    monkeypatch.setattr(orchestrator_module, "research_agent", MagicMock(return_value="research results"))
    monkeypatch.setattr(orchestrator_module, "fact_checking_agent", MagicMock(return_value="fact check results"))
    monkeypatch.setattr(orchestrator, "create_plan", MagicMock(return_value="a plan"))
    monkeypatch.setattr(orchestrator, "results_acceptable", MagicMock(return_value=(True, "a plan")))

    with pytest.raises(Exception):
        orchestrator.run("what is nvidia stock price")
