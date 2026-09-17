import logging
import re
import httpx
from config import GUARDIAN_API_KEY, NEWS_SEARCH_MAX_ARTICLES, NEWS_SEARCH_MAX_BODY_CHARS

logger = logging.getLogger(__name__)

_GUARDIAN_SEARCH_URL = "https://content.guardianapis.com/search"

NEWS_SEARCH_TOOL_DECLARATION: dict = {
    "type": "function",
    "name": "search_news",
    "description": "Searches recent news articles from The Guardian for a given topic and returns headlines, publish dates, source URLs, and full article text. Use this instead of general web search when you specifically want dated, sourced news coverage.",
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


def _strip_html(html: str) -> str:
    """The Guardian's article body field is HTML - this is a plain tag-stripping pass (not a
    full HTML parser), sufficient for the fairly clean paragraph markup Guardian articles use."""
    return re.sub(r"<[^>]+>", "", html).strip()


def search_news(query: str) -> dict:
    """Searches The Guardian's Open Platform for recent articles matching query. This is the
    implementation dispatched for the "search_news" function tool declared above - see
    NEWS_SEARCH_TOOL_DECLARATION and research_agent.py's _TOOL_DISPATCH.
    Args:
        query <str>: The search query
    Returns:
        <dict>: {"articles": [{"headline", "published_at", "url", "body"}, ...]} on success,
            or {"error": "..."} if the API key isn't configured or the request fails
    """
    if not GUARDIAN_API_KEY:
        return {"error": "GUARDIAN_API_KEY is not configured"}

    try:
        response = httpx.get(
            _GUARDIAN_SEARCH_URL,
            params={
                "q": query,
                "api-key": GUARDIAN_API_KEY,
                "show-fields": "headline,body",
                "order-by": "relevance",
                "page-size": NEWS_SEARCH_MAX_ARTICLES,
            },
            timeout=15,
        )
        response.raise_for_status()
    except httpx.HTTPError as e:
        logger.warning("search_news request failed for query %r: %s", query, e)
        return {"error": f"news search failed: {e}"}

    results = response.json().get("response", {}).get("results", [])
    return {
        "articles": [
            {
                "headline": result.get("webTitle"),
                "published_at": result.get("webPublicationDate"),
                "url": result.get("webUrl"),
                "body": _strip_html(result.get("fields", {}).get("body", ""))[:NEWS_SEARCH_MAX_BODY_CHARS],
            }
            for result in results
        ]
    }
