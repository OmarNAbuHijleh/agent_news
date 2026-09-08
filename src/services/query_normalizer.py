from google import genai
from ..agents.retry import call_with_retry

_normalizer_prompt: str = """You are a query normalizer for a research-caching system. Rewrite the user's query into a short, canonical form so that semantically equivalent queries map to the exact same text, regardless of how they were originally phrased.

Rules:
- Output ONLY the canonical query text - no punctuation at the end, no quotes, no explanation.
- Use lowercase.
- Prefer a consistent, official name for the subject (e.g. always "nvidia", not "nvda" or "Nvidia Corp").
- Strip filler words and politeness (e.g. "can you tell me", "please", "what's the latest on").
- Preserve the specific subject and intent of the query - do not generalize or drop meaningful qualifiers.
"""


def normalize_query(client: genai.Client, raw_query: str) -> str:
    """Rewrites a raw user query into a canonical form suitable for use as a cache key.
    Args:
        client <genai.Client>: The shared client for this session
        raw_query <str>: The user's original query
    Returns:
        <str>: The canonicalized query. Falls back to a simple lowercase/trim of raw_query if the model returns nothing
    """
    response = call_with_retry(lambda: client.interactions.create(
        model="gemini-3.1-flash-lite",
        system_instruction=_normalizer_prompt,
        input=raw_query,
    ), stage="query_normalizer")
    return (response.output_text or raw_query).strip().lower()
