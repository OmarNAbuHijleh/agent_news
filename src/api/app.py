import json
import logging
from collections.abc import Iterator
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from config import GEMINI_API_KEY
from ..services.cached_research_service import CachedResearchService
from ..agents.progress_event import ProgressEvent

logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic News Research API")


class ResearchRequest(BaseModel):
    query: str


def _format_as_sse(event: ProgressEvent) -> str:
    payload = json.dumps({"stage": event.stage, "content": event.content, "done": event.done})
    return f"data: {payload}\n\n"


def _stream_research(query: str) -> Iterator[str]:
    service = CachedResearchService(GEMINI_API_KEY)
    for event in service.run_streaming(query):
        yield _format_as_sse(event)


@app.post("/api/research")
def research(request: ResearchRequest) -> StreamingResponse:
    """Streams research progress for a query as Server-Sent Events, one `data: {...}` message
    per ProgressEvent, so a client can show real content instead of waiting silently."""
    return StreamingResponse(_stream_research(request.query), media_type="text/event-stream")


# Mounted last (and at "/") so it only catches requests the routes above didn't already match.
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host="127.0.0.1", port=8000)
