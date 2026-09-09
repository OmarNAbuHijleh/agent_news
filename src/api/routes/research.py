import json
import logging
from collections.abc import Iterator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from config import GEMINI_API_KEY
from ...services.cached_research_service import CachedResearchService
from ...agents.progress_event import ProgressEvent
from ..rate_limiter import limiter, RESEARCH_RATE_LIMIT

logger = logging.getLogger(__name__)

router = APIRouter()


class ResearchQuery(BaseModel):
    query: str


def _format_as_sse(event: ProgressEvent) -> str:
    payload = json.dumps({"stage": event.stage, "content": event.content, "done": event.done})
    return f"data: {payload}\n\n"


def _stream_research(query: str) -> Iterator[str]:
    service = CachedResearchService(GEMINI_API_KEY)
    for event in service.run_streaming(query):
        yield _format_as_sse(event)


@router.post("/research")
@limiter.limit(RESEARCH_RATE_LIMIT)
def research(request: Request, payload: ResearchQuery) -> StreamingResponse:
    """Streams research progress for a query as Server-Sent Events, one `data: {...}` message
    per ProgressEvent, so a client can show real content instead of waiting silently.
    Rate-limited per client IP (see rate_limiter.py) since each request can trigger a
    multi-minute, real-money pipeline run.
    """
    return StreamingResponse(_stream_research(payload.query), media_type="text/event-stream")
