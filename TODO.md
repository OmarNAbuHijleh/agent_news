# TODO
## Purpose
This document functions as a tracker for open items that need implementation.

## Open Items
- Tool calls for research (custom tools beyond google_search/url_context — `research_agent.py`'s `_TOOLS[tool_call.name]` dispatch is still unimplemented/broken for custom functions; pinned by a `pytest.mark.xfail` regression test in `test/agents/test_research_agent.py`)
- Unit tests for `src/api/` once it's built
- API development (versioning, middleware, logging)
- Frontend development
- Query cache is currently a local SQLite file (`query_cache.sqlite3`); move to a hosted store (DynamoDB/ElastiCache per the README's original architecture) once there's an actual deployment to share it across
