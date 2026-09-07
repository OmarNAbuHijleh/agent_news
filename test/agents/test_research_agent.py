from unittest.mock import MagicMock
import pytest
import src.agents.research_agent as research_agent_module
from src.agents.research_agent import research_agent


def test_research_agent_returns_output_when_no_tool_calls(make_interaction):
    """This is the common case observed in real runs: google_search/url_context are Google's
    built-in tools and run server-side, so the model returns a final answer directly without
    ever surfacing a function_call step."""
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="final research result", steps=[])

    result = research_agent(client, "do some research")

    assert "final research result" in result
    client.interactions.create.assert_called_once()


def test_research_agent_passes_plan_and_bounded_output_tokens(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="result", steps=[])

    research_agent(client, "investigate topic X")

    _, kwargs = client.interactions.create.call_args
    assert kwargs["model"] == "gemini-3.7-flash"
    assert kwargs["input"] == "investigate topic X"
    assert kwargs["generation_config"]["max_output_tokens"] > 0


def test_research_agent_stops_at_tool_round_cap_without_dispatching(make_interaction, make_function_call_step, monkeypatch):
    """Regression test for the (currently unbounded-by-default) tool-call loop: with the round
    cap already reached, the loop must stop before attempting to dispatch any tool call."""
    monkeypatch.setattr(research_agent_module, "MAX_RESEARCH_AGENT_TOOL_ROUNDS", 0)
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(
        output_text="thinking...",
        steps=[make_function_call_step(name="google_search")],
    )

    result = research_agent(client, "do some research")

    assert "thinking..." in result
    client.interactions.create.assert_called_once()  # capped before any tool round could run


@pytest.mark.xfail(reason="_TOOLS is a list, not a dict, so _TOOLS[tool_call.name] raises TypeError. "
                          "Custom tool dispatch is not implemented yet (see TODO.md 'Tool calls for research'). "
                          "Update/remove this test once that's implemented.", strict=True)
def test_research_agent_tool_dispatch_not_yet_implemented(make_interaction, make_function_call_step):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(
        output_text="thinking...",
        steps=[make_function_call_step(name="google_search")],
    )

    research_agent(client, "do some research")
