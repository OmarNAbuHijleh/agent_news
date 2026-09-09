from unittest.mock import MagicMock
from src.agents.investigation_qa_agent import investigation_qa_agent


def test_investigation_qa_agent_returns_output_text(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="the answer")

    result = investigation_qa_agent(client, "evidence text", "why?")

    assert result == "the answer"


def test_investigation_qa_agent_includes_context_and_question_in_input(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="the answer")

    investigation_qa_agent(client, "nvidia gross margin is 75%", "why is the margin so high?")

    _, kwargs = client.interactions.create.call_args
    assert "nvidia gross margin is 75%" in kwargs["input"]
    assert "why is the margin so high?" in kwargs["input"]
    assert kwargs["model"] == "gemini-3.1-flash-lite"
