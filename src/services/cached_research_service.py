import json
import logging
from typing import Iterator
from google import genai
from .query_cache import QueryCache
from .query_normalizer import normalize_query
from .trending_topics import TrendingTopics
from ..agents.research_orchestrator import ResearchOrchestrator
from ..agents.progress_event import ProgressEvent

logger = logging.getLogger(__name__)

# Transient progress-status events (e.g. "Researching...") carry no real evidence - excluded
# from what gets cached/replayed so a cache hit shows the actual evidence trail (plan,
# findings, fact-check, final report) without stale "still working" filler.
_STATUS_ONLY_STAGES = frozenset({"planning", "researching", "fact_checking", "synthesizing"})


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
        self._trending = TrendingTopics()

    def run_streaming(self, user_input_query: str) -> Iterator[ProgressEvent]:
        """Given a user query, replays the full cached evidence trail (plan, research findings,
        and fact-checking, not just the final report) on a cache hit, otherwise streams the
        full research pipeline's progress and caches that same evidence trail once it's ready.
        Args:
            user_input_query <str>: The user's original query
        Yields:
            <ProgressEvent>: Progress updates, ending with a done=True event carrying the final result
        """
        normalized_query = normalize_query(self._client, user_input_query)
        # Counts toward "trending" regardless of hit/miss - popularity is about how often a
        # topic is asked, not how often the pipeline actually had to run.
        self._trending.record_query(normalized_query)

        cached_events = self._get_cached_events(normalized_query)
        if cached_events is not None:
            logger.info("cache hit for normalized query: %r", normalized_query)
            yield ProgressEvent(stage="cache_hit_notice", content="Serving a cached investigation into this topic.")
            yield from cached_events
            return

        logger.info("cache miss for normalized query: %r", normalized_query)
        evidence_events: list[ProgressEvent] = []
        for event in self._orchestrator.run_streaming(user_input_query):
            yield event
            if event.stage not in _STATUS_ONLY_STAGES:
                evidence_events.append(event)
        self._cache.set(normalized_query, self._serialize_events(evidence_events))

    def _get_cached_events(self, normalized_query: str) -> list[ProgressEvent] | None:
        cached_json = self._cache.get(normalized_query)
        if cached_json is None:
            return None
        try:
            return [ProgressEvent(**event) for event in json.loads(cached_json)]
        except (json.JSONDecodeError, TypeError):
            logger.warning("discarding unparseable cache entry for %r", normalized_query)
            return None

    @staticmethod
    def _serialize_events(events: list[ProgressEvent]) -> str:
        return json.dumps([{"stage": event.stage, "content": event.content, "done": event.done} for event in events])

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
