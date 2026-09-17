import json
from collections.abc import Callable
from ...services.query_cache import QueryCache
from config import CACHE_TTL_SECONDS

# Reuses QueryCache (a generic string cache, despite living under services/) rather than a
# second cache implementation. Same TTL as investigation results (CACHE_TTL_SECONDS) per
# explicit decision - news content doesn't shift meaningfully over that window either. Keys are
# prefixed with the tool name so this can't collide with QueryCache's own investigation-result
# keys (plain user query text) even though it's the same underlying SQLite file/table.
_cache = QueryCache(ttl_seconds=CACHE_TTL_SECONDS)


def cached_tool_call(tool_name: str, query: str, fetch: Callable[[], dict]) -> dict:
    """Caches a custom tool's result by (tool_name, query) so repeated/near-identical searches -
    within one investigation's re-planning loop, or across separate investigations - don't
    re-hit a metered, free-tier news API for the same thing.
    Args:
        tool_name <str>: The dispatch name of the calling tool, e.g. "search_news"
        query <str>: The tool's search query, used as (part of) the cache key
        fetch <Callable[[], dict]>: Zero-argument callable that performs the real API call and
            returns the result dict, only invoked on a cache miss
    Returns:
        <dict>: The (possibly cached) tool result
    """
    key = f"tool:{tool_name}:{query.strip().lower()}"
    cached = _cache.get(key)
    if cached is not None:
        return json.loads(cached)

    result = fetch()
    # Don't cache errors (missing key, HTTP failure, etc.) for a week - those are almost always
    # transient or config issues that should be retried on the next call, not frozen in place.
    if "error" not in result:
        _cache.set(key, json.dumps(result))
    return result
