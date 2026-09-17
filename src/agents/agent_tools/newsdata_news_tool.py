import logging
import httpx
from config import NEWSDATA_IO_API_KEY, NEWSDATA_MAX_ARTICLES

logger = logging.getLogger(__name__)

_NEWSDATA_LATEST_URL = "https://newsdata.io/api/1/latest"

NEWSDATA_NEWS_TOOL_DECLARATION: dict = {
    "type": "function",
    "name": "search_newsdata_news",
    "description": "Searches recent English-language news articles across many publishers via NewsData.io and returns headlines, publish dates, source names/URLs, and a short description. Broader multi-publisher coverage than search_news (The Guardian), but only a snippet, not full article text - use search_news first when you need full article body, use this for wider source diversity or when Guardian has no relevant results.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query, e.g. a company, person, or event name.",
            },
        },
        "required": ["query"],
    },
}


def search_newsdata_news(query: str) -> dict:
    """Searches NewsData.io for recent English-language articles matching query. This is the
    implementation dispatched for the "search_newsdata_news" function tool declared above - see
    NEWSDATA_NEWS_TOOL_DECLARATION and research_agent.py's _TOOL_DISPATCH.
    Args:
        query <str>: The search query
    Returns:
        <dict>: {"articles": [{"headline", "published_at", "source", "url", "description"}, ...]}
            on success, or {"error": "..."} if the API key isn't configured or the request fails
    """
    if not NEWSDATA_IO_API_KEY:
        return {"error": "NEWSDATA_IO_API_KEY is not configured"}

    try:
        response = httpx.get(
            _NEWSDATA_LATEST_URL,
            params={
                "apikey": NEWSDATA_IO_API_KEY,
                "q": query,
                "language": "en",
                "size": NEWSDATA_MAX_ARTICLES,
            },
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("search_newsdata_news request failed for query %r: %s", query, e)
        return {"error": f"news search failed: {e}"}

    results = response.json().get("results", [])
    return {
        "articles": [
            {
                "headline": result.get("title"),
                "published_at": result.get("pubDate"),
                "source": result.get("source_name"),
                "url": result.get("link"),
                "description": result.get("description"),
            }
            for result in results
        ]
    }
