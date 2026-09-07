# TODO
## Purpose
This document functions as a tracker for open items that need implementation.

## Open Items
- Tool calls for research (custom tools beyond google_search/url_context — `research_agent.py`'s `_TOOLS[tool_call.name]` dispatch is still unimplemented/broken for custom functions; pinned by a `pytest.mark.xfail` regression test in `test/agents/test_research_agent.py`)
- Unit tests for `src/api/` and `src/services/` once those are built
- API development (versioning, middleware, logging)
- Frontend development
