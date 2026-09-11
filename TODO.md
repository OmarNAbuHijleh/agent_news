# TODO
## Purpose
This document functions as a tracker for open items that need implementation.

## Open Items
- Tool calls for research (custom tools beyond google_search/url_context — `research_agent.py`'s `_TOOLS[tool_call.name]` dispatch is still unimplemented/broken for custom functions; pinned by a `pytest.mark.xfail` regression test in `test/agents/test_research_agent.py`)
- API hardening still open: auth (currently unauthenticated - anyone who can reach the server can trigger paid research runs). (Versioning, rate-limiting, structured request logging, and CORS are done - see `src/api/routes/`, `rate_limiter.py`, `request_logging_middleware.py`, `app.py`'s `CORSMiddleware`. CORS is configured but inert by default - set `CORS_ALLOWED_ORIGINS` once the frontend is ever served from a different origin than the API)
- Query cache is currently a local SQLite file (`query_cache.sqlite3`). A DynamoDB-backed drop-in replacement exists at `src/services/cloud_query_cache.py` (`DynamoDBQueryCache`) but is dead code - not wired into `CachedResearchService` yet. Activate it once there's an actual deployment to share the cache across: provision the DynamoDB table (see that file's docstring), `pip install .[cloud]`, and swap `QueryCache()` for `DynamoDBQueryCache(...)` in `CachedResearchService.__init__`
- Frontend is intentionally minimal (single page, no build tooling) - revisit if the README's "Trending Investigations" feature gets built, since that needs more than one page/view
- "Ask the Investigation" keeps evidence client-side only (in a JS variable) for the current browser session - reload the page or close the tab and it's gone, and there's no way to revisit a past investigation. Would need server-side persistence (tied into the query cache work) to fix
- Actual cloud deployment (Lambda/CloudWatch/etc. per the README) - everything, including the API, still only runs locally via `python -m src.api.app`
