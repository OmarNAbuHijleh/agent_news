from unittest.mock import MagicMock
from src.agents.agent_type_enum import AgentType
from src.agents.research_step import ResearchStep
from src.agents.synthesis_agent import synthesis_agent


def test_synthesis_agent_returns_output_text(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="final summary")

    result = synthesis_agent(client, [ResearchStep(AgentType.RESEARCH_PLANNER, "plan text")])

    assert result == "final summary"


def test_synthesis_agent_flattens_research_history_into_input_string(make_interaction):
    """Regression test: passing the raw list of ResearchStep objects as `input` fails against
    the real API - it must be flattened to text first (see CHANGELOG 0.1.5)."""
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="final summary")
    steps = [
        ResearchStep(AgentType.RESEARCH_PLANNER, "plan text"),
        ResearchStep(AgentType.RESEARCHER, "research text"),
    ]

    synthesis_agent(client, steps)

    _, kwargs = client.interactions.create.call_args
    assert isinstance(kwargs["input"], str)
    assert "plan text" in kwargs["input"]
    assert "research text" in kwargs["input"]
