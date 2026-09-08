import logging
from typing import Iterator
from google import genai
from .query_cache import QueryCache
from .query_normalizer import normalize_query
from ..agents.research_orchestrator import ResearchOrchestrator
from ..agents.progress_event import ProgressEvent

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
        # Local SQLite cache for now. A DynamoDB-backed drop-in replacement exists at
        # cloud_query_cache.DynamoDBQueryCache (same get/set/close interface, currently unused/
        # dead code) - swap it in here once there's an actual deployment to share the cache
        # across.
        self._cache = QueryCache()

    def run_streaming(self, user_input_query: str) -> Iterator[ProgressEvent]:
        """Given a user query, yields a single done=True event with the cached result on a
        cache hit, otherwise streams the full research pipeline's progress and caches the
        final result once it's ready.
        Args:
            user_input_query <str>: The user's original query
        Yields:
            <ProgressEvent>: Progress updates, ending with a done=True event carrying the result
        """
        normalized_query = normalize_query(self._client, user_input_query)

        cached_result = self._cache.get(normalized_query)
        if cached_result is not None:
            logger.info("cache hit for normalized query: %r", normalized_query)
            yield ProgressEvent(stage="cache_hit", content=cached_result, done=True)
            return

        logger.info("cache miss for normalized query: %r", normalized_query)
        final_result = ""
        for event in self._orchestrator.run_streaming(user_input_query):
            yield event
            if event.done:
                final_result = event.content
        self._cache.set(normalized_query, final_result)

    def run(self, user_input_query: str) -> str:
        """Given a user query, returns a cached result if one exists and hasn't expired,
        otherwise runs the full research pipeline and caches the result.
        Args:
            user_input_query <str>: The user's original query
        Returns:
            <str>: The (possibly cached) synthesized research result
        """
        final_result = ""
        for event in self.run_streaming(user_input_query):
            if event.done:
                final_result = event.content
        return final_result
