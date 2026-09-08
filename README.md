# README

## Purpose
This repository contains the code for a news research agent. Given a topic, it will:
- investigate across multiple sources
- identify the factual core
- detect disagreements
- reconstruct the timeline
- explain what is known vs. what is uncertain

## Structure [in progress]
### Agents involved:
1. Research Planner
2. Research Agent
3. Evidence/Fact Checking Agent
4. Synthesis Agent (Produces the final report)

### Under the Hood
Chain of thought is exposed and visible for all to see - the frontend streams each stage (plan, research findings, fact-check, final report) to the user as it completes rather than showing only the finished report. Still to fully expose: individual tool calls/searches within a stage, per-claim confidence, and execution time.

### Tools I intent to use:
- python and its accompanying libraries (see "pyproject.toml")
- AWS lambda (for API), DynamoDB/ElastiCache, Cloudwatch - not deployed yet; the API currently runs locally via FastAPI/uvicorn (`python -m src.api.app`)
- LLM API: Google Gemini (`google-genai`)
- search/news API - not yet; research currently relies on Gemini's built-in `google_search`/`url_context` tools


### Cost Saving
I'm not made of money, so I'd like to keep as much of what I have as possible. I'm following this architecture so that I can cache the redundant searches (implemented in `src/services/`, currently backed by a local SQLite file rather than a hosted DB - see file structure above):
```text
User
  │
  ▼
Query Normalizer
  │
  ▼
Cache / Database
/          \
HIT            MISS
│               │
▼               ▼
Return result     Run agents
           │
           ▼
        Cache
```

## Features
- Trending Investigations: This is going to be a page that tracks what is currently trending and will fire an update for those topics occasionally.
- Ask the Investigation: Following the synthesizing of a report, we'll give users the ability to ask follow up questions and discuss the results.
  - For example:
    1. User: "Why does the report say NVIDIA's position is strengthening?"
    2. The system performs RAG over the investigation's evidence and responds: "The conclusion is primarily based on sources A, B and C..."
    3. "What evidence contradicts that?"
    4. The system retrieves the contradictory evidence and provides it


## Project File Structure
```
root_dir/
├── pyproject.toml
├── uv.lock
├── README.md
├── CHANGELOG.md
├── TODO.md
├── config.py                       # Environment/configuration (GEMINI_API_KEY, MAX_RESEARCH_ITERATIONS, CACHE_DB_PATH, CACHE_TTL_SECONDS)
├── .env
├── .gitignore
├── query_cache.sqlite3             # Local query-result cache (gitignored, created on first run)
│
├── frontend/                       # Static single-page UI (no build step) - served by src/api/app.py
│   ├── index.html
│   ├── style.css
│   └── app.js                      # Reads the /api/research SSE stream and renders each stage as it arrives
│
├── src/
│   ├── __init__.py
│   ├── main.py                     # CLI entry point (blocking, prints the final result only)
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── agent_type_enum.py      # AgentType enum, tags each research step
│   │   ├── research_step.py        # ResearchStep dataclass (agent_type + content)
│   │   ├── research_utils.py       # Flattens ResearchStep history into model input
│   │   ├── progress_event.py       # ProgressEvent dataclass (stage, content, done) for streaming
│   │   ├── retry.py                # Rate-limit retry/backoff wrapper for API calls
│   │   ├── research_orchestrator.py# ResearchOrchestrator: owns the shared client; run_streaming() yields ProgressEvents, run() wraps it and returns just the final result
│   │   ├── research_agent.py
│   │   ├── fact_checking_agent.py
│   │   ├── synthesis_agent.py
│   │   └── agent_tools/            # Custom tools for the research agent (planned, not yet implemented)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py                  # FastAPI app: POST /api/research streams ProgressEvents as SSE; also serves frontend/. Run with `python -m src.api.app`
│   │
│   └── services/
│       ├── __init__.py
│       ├── query_normalizer.py     # LLM call that canonicalizes a raw query into a cache key
│       ├── query_cache_base.py     # QueryCacheBackend protocol shared by every cache backend
│       ├── query_cache.py          # SQLite-backed cache of research results, keyed by normalized query (active)
│       ├── cloud_query_cache.py    # DynamoDB-backed cache, same interface (DEAD CODE - not wired in yet, see docstring)
│       └── cached_research_service.py  # Wires normalizer + cache + ResearchOrchestrator together; run_streaming() drives the API, run() drives main.py
│
└── test/                           # Unit tests, mirroring src/ (mocks the google-genai client and FastAPI's TestClient - no real API calls)
```
