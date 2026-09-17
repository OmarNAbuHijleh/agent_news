import json
from unittest.mock import MagicMock
import src.agents.research_agent as research_agent_module
from src.agents.research_agent import research_agent
from src.agents.tool_call_budget import ToolCallBudget


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


def test_research_agent_declares_the_news_search_tools(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="result", steps=[])

    research_agent(client, "investigate topic X")

    _, kwargs = client.interactions.create.call_args
    function_tool_names = [tool.get("name") for tool in kwargs["tools"] if isinstance(tool, dict) and tool.get("type") == "function"]
    assert "search_news" in function_tool_names
    assert "search_newsdata_news" in function_tool_names


def test_research_agent_stops_at_tool_round_cap_without_dispatching(make_interaction, make_function_call_step, monkeypatch):
    """Regression test for the tool-call loop: with the round cap already reached, the loop
    must stop before attempting to dispatch any tool call."""
    monkeypatch.setattr(research_agent_module, "MAX_RESEARCH_AGENT_TOOL_ROUNDS", 0)
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(
        output_text="thinking...",
        steps=[make_function_call_step(name="search_news")],
    )

    result = research_agent(client, "do some research")

    assert "thinking..." in result
    client.interactions.create.assert_called_once()  # capped before any tool round could run


# --- tool dispatch (regression coverage for the _TOOLS[tool_call.name] bug) ---

def test_research_agent_dispatches_a_registered_custom_tool_by_name(make_interaction, make_function_call_step, monkeypatch):
    fake_search_news = MagicMock(return_value={"articles": [{"headline": "Big News"}]})
    monkeypatch.setattr(research_agent_module, "_TOOL_DISPATCH", {"search_news": fake_search_news})

    client = MagicMock()
    client.interactions.create.side_effect = [
        make_interaction(output_text="thinking...", steps=[make_function_call_step(name="search_news", id="call-1", arguments={"query": "nvidia"})]),
        make_interaction(output_text="done", steps=[]),
    ]

    result = research_agent(client, "do some research")

    fake_search_news.assert_called_once_with(query="nvidia")
    assert "done" in result


def test_research_agent_feeds_the_dispatch_result_back_as_a_function_result(make_interaction, make_function_call_step, monkeypatch):
    fake_search_news = MagicMock(return_value={"articles": [{"headline": "Big News"}]})
    monkeypatch.setattr(research_agent_module, "_TOOL_DISPATCH", {"search_news": fake_search_news})

    client = MagicMock()
    client.interactions.create.side_effect = [
        make_interaction(output_text="thinking...", steps=[make_function_call_step(name="search_news", id="call-1", arguments={"query": "nvidia"})]),
        make_interaction(output_text="done", steps=[]),
    ]

    research_agent(client, "do some research")

    second_call_kwargs = client.interactions.create.call_args_list[1].kwargs
    fed_back = second_call_kwargs["input"]
    assert fed_back[0]["call_id"] == "call-1"
    assert fed_back[0]["name"] == "search_news"
    assert json.loads(fed_back[0]["result"][0]["text"]) == {"articles": [{"headline": "Big News"}]}


def test_research_agent_returns_an_error_result_for_an_unrecognized_tool_name(make_interaction, make_function_call_step, monkeypatch):
    monkeypatch.setattr(research_agent_module, "_TOOL_DISPATCH", {})

    client = MagicMock()
    client.interactions.create.side_effect = [
        make_interaction(output_text="thinking...", steps=[make_function_call_step(name="some_unregistered_tool", id="call-1")]),
        make_interaction(output_text="done", steps=[]),
    ]

    research_agent(client, "do some research")

    second_call_kwargs = client.interactions.create.call_args_list[1].kwargs
    fed_back = second_call_kwargs["input"]
    assert json.loads(fed_back[0]["result"][0]["text"]) == {"error": "unknown tool: some_unregistered_tool"}


def test_research_agent_does_not_dispatch_once_the_tool_budget_is_exhausted(make_interaction, make_function_call_step, monkeypatch):
    fake_search_news = MagicMock(return_value={"articles": ["should not be reached"]})
    monkeypatch.setattr(research_agent_module, "_TOOL_DISPATCH", {"search_news": fake_search_news})
    exhausted_budget = ToolCallBudget(max_calls=0)

    client = MagicMock()
    client.interactions.create.side_effect = [
        make_interaction(output_text="thinking...", steps=[make_function_call_step(name="search_news", id="call-1", arguments={"query": "nvidia"})]),
        make_interaction(output_text="done", steps=[]),
    ]

    research_agent(client, "do some research", tool_budget=exhausted_budget)

    fake_search_news.assert_not_called()
    second_call_kwargs = client.interactions.create.call_args_list[1].kwargs
    fed_back = second_call_kwargs["input"]
    assert "budget exhausted" in fed_back[0]["result"][0]["text"]


def test_research_agent_shares_the_tool_budget_across_multiple_calls_within_it(make_interaction, make_function_call_step, monkeypatch):
    fake_search_news = MagicMock(return_value={"articles": []})
    monkeypatch.setattr(research_agent_module, "_TOOL_DISPATCH", {"search_news": fake_search_news})
    shared_budget = ToolCallBudget(max_calls=1)

    client = MagicMock()
    client.interactions.create.side_effect = [
        make_interaction(output_text="thinking...", steps=[make_function_call_step(name="search_news", id="call-1", arguments={"query": "nvidia"})]),
        make_interaction(output_text="done", steps=[]),
    ]
    research_agent(client, "do some research", tool_budget=shared_budget)

    client.interactions.create.side_effect = [
        make_interaction(output_text="thinking...", steps=[make_function_call_step(name="search_news", id="call-2", arguments={"query": "tesla"})]),
        make_interaction(output_text="done", steps=[]),
    ]
    research_agent(client, "do some other research", tool_budget=shared_budget)

    fake_search_news.assert_called_once()  # second research_agent() call found the budget already spent
