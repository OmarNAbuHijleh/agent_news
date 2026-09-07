from unittest.mock import MagicMock
from src.agents.fact_checking_agent import fact_checking_agent


def test_fact_checking_agent_returns_output_text(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="fact check result")

    result = fact_checking_agent(client, "some research results")

    assert result == "fact check result"


def test_fact_checking_agent_passes_input_not_user_content(make_interaction):
    """Regression test: client.interactions.create() has no `user_content` parameter - it
    raises TypeError. The research results must be passed as `input`."""
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="fact check result")

    fact_checking_agent(client, "some research results")

    _, kwargs = client.interactions.create.call_args
    assert kwargs["input"] == "some research results"
    assert "user_content" not in kwargs


def test_fact_checking_agent_uses_a_real_model_name(make_interaction):
    """Regression test: "gemini-3.1-flash" does not exist and returns a 404. See
    CHANGELOG 0.1.7 - keep this in sync with fact_checking_agent.py's model."""
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="fact check result")

    fact_checking_agent(client, "some research results")

    _, kwargs = client.interactions.create.call_args
    assert kwargs["model"] == "gemini-3.6-flash"
