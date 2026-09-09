from google import genai
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from config import GEMINI_API_KEY
from ...agents.investigation_qa_agent import investigation_qa_agent
from ..rate_limiter import limiter, RESEARCH_RATE_LIMIT

router = APIRouter()


class AskQuery(BaseModel):
    context: str = Field(min_length=1)
    question: str = Field(min_length=1)


class AskAnswer(BaseModel):
    answer: str


@router.post("/ask")
@limiter.limit(RESEARCH_RATE_LIMIT)
def ask(request: Request, payload: AskQuery) -> AskAnswer:
    """Answers a follow-up question about a completed investigation. Unlike /research, this is
    a single LLM call grounded in the evidence the client already has (see investigation_qa_agent),
    so it's a normal blocking JSON response rather than a stream - no multi-stage pipeline to
    show progress for. Rate-limited per client IP for the same reason as /research: real cost
    per call.
    """
    client = genai.Client(api_key=GEMINI_API_KEY)
    answer = investigation_qa_agent(client, payload.context, payload.question)
    return AskAnswer(answer=answer)
