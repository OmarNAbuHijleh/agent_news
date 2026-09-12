from fastapi import APIRouter
from pydantic import BaseModel
from config import TRENDING_TOPICS_LIMIT
from ...services.trending_topics import TrendingTopics

router = APIRouter()


class TrendingTopicsResponse(BaseModel):
    topics: list[str]


@router.get("/trending")
def trending() -> TrendingTopicsResponse:
    """Returns the most-asked-about topics from this app's own query history (see
    TrendingTopics) - a cheap local read, not an LLM call, so it isn't rate-limited like
    /research and /ask.
    """
    topics = TrendingTopics().get_top(TRENDING_TOPICS_LIMIT)
    return TrendingTopicsResponse(topics=topics)
