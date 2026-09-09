# TODO
## Purpose
This document functions as a tracker for open items that need implementation.

## Open Items
- Tool calls for research (custom tools beyond google_search/url_context — `research_agent.py`'s `_TOOLS[tool_call.name]` dispatch is still unimplemented/broken for custom functions; pinned by a `pytest.mark.xfail` regression test in `test/agents/test_research_agent.py`)
- API hardening still open: auth (currently unauthenticated - anyone who can reach the server can trigger paid research runs), CORS if the frontend is ever split onto a different origin. (Versioning, rate-limiting, and structured request logging are done - see `src/api/routes/`, `rate_limiter.py`, `request_logging_middleware.py`)
- Query cache is currently a local SQLite file (`query_cache.sqlite3`). A DynamoDB-backed drop-in replacement exists at `src/services/cloud_query_cache.py` (`DynamoDBQueryCache`) but is dead code - not wired into `CachedResearchService` yet. Activate it once there's an actual deployment to share the cache across: provision the DynamoDB table (see that file's docstring), `pip install .[cloud]`, and swap `QueryCache()` for `DynamoDBQueryCache(...)` in `CachedResearchService.__init__`
- Frontend is intentionally minimal (single page, no build tooling) - revisit if the README's "Trending Investigations" / "Ask the Investigation" features get built, since those need more than one page/view
- Actual cloud deployment (Lambda/CloudWatch/etc. per the README) - everything, including the API, still only runs locally via `python -m src.api.app`
