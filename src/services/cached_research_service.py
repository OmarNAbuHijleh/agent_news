import logging
from google import genai
from .query_cache import QueryCache
from .query_normalizer import normalize_query
from ..agents.research_orchestrator import ResearchOrchestrator

logger = logging.getLogger(__name__)


class CachedResearchService:
    """Wraps ResearchOrchestrator with the query-normalizer + cache layer described in the
    README's cost-saving architecture: normalize the query, check the cache, and only run the
    full (expensive) agent pipeline on a miss.

    One instance holds one genai.Client, shared between the normalizer and the orchestrator.
    """

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)
        self._orchestrator = ResearchOrchestrator(client=self._client)
        self._cache = QueryCache()

    def run(self, user_input_query: str) -> str:
        """Given a user query, returns a cached result if one exists and hasn't expired,
        otherwise runs the full research pipeline and caches the result.
        Args:
            user_input_query <str>: The user's original query
        Returns:
            <str>: The (possibly cached) synthesized research result
        """
        normalized_query = normalize_query(self._client, user_input_query)

        cached_result = self._cache.get(normalized_query)
        if cached_result is not None:
            logger.info("cache hit for normalized query: %r", normalized_query)
            return cached_result

        logger.info("cache miss for normalized query: %r", normalized_query)
        result = self._orchestrator.run(user_input_query)
        self._cache.set(normalized_query, result)
        return result
