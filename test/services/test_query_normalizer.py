from unittest.mock import MagicMock
from src.services.query_normalizer import normalize_query


def test_normalize_query_returns_the_model_output_lowercased_and_trimmed(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="  Nvidia Stock Price  ")

    result = normalize_query(client, "what's NVDA doing today?")

    assert result == "nvidia stock price"


def test_normalize_query_passes_raw_query_as_input(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text="nvidia stock price")

    normalize_query(client, "what's NVDA doing today?")

    _, kwargs = client.interactions.create.call_args
    assert kwargs["input"] == "what's NVDA doing today?"
    assert kwargs["model"] == "gemini-3.1-flash-lite"


def test_normalize_query_falls_back_to_raw_query_when_model_returns_nothing(make_interaction):
    client = MagicMock()
    client.interactions.create.return_value = make_interaction(output_text=None)

    result = normalize_query(client, "  What's NVDA Doing Today?  ")

    assert result == "what's nvda doing today?"
