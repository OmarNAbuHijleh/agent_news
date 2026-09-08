# CHANGELOG

## [0.1.10] - 2026-09-08
Added:
- `src/services/query_cache_base.py`: `QueryCacheBackend`, a `typing.Protocol` formalizing the get/set/close interface shared by every cache backend, so `CachedResearchService` can swap backends without other code changing
- `src/services/cloud_query_cache.py`: `DynamoDBQueryCache`, a DynamoDB-backed drop-in replacement for the local SQLite `QueryCache`, per the README's original cost-saving architecture. **Dead code - not wired into `CachedResearchService` yet**; see that file's docstring for activation steps
- `boto3` added as an optional `cloud` dependency group (`pip install .[cloud]`), not part of the default install since the DynamoDB backend isn't active
- `CACHE_DYNAMODB_TABLE_NAME` and `CACHE_AWS_REGION` config values (unused until the cloud backend is activated)
- Unit tests for `DynamoDBQueryCache`, fully mocking `boto3.resource` - no real AWS calls or credentials needed

## [0.1.9] - 2026-09-08
Added:
- `src/services/query_normalizer.py`: LLM call (gemini-3.1-flash-lite) that canonicalizes a raw query into a cache key, catching paraphrases like "how's NVDA doing" vs "nvidia stock price"
- `src/services/query_cache.py`: SQLite-backed cache of research results keyed by normalized query, with a configurable TTL (`CACHE_TTL_SECONDS`, default 1 week - news/market context doesn't shift meaningfully over a few days) so stale results don't get served indefinitely
- `src/services/cached_research_service.py`: `CachedResearchService`, wiring normalizer + cache + `ResearchOrchestrator` together per the README's cost-saving architecture (normalize -> check cache -> hit returns cached result, miss runs the full agent pipeline and caches it)
- `CACHE_DB_PATH` and `CACHE_TTL_SECONDS` config values; `*.sqlite3` added to `.gitignore`
- Unit tests for all three new modules (`test/services/`)

Changed:
- `ResearchOrchestrator.__init__` now accepts an optional pre-built `client` in addition to `api_key`, so `CachedResearchService` can share one `genai.Client` between the normalizer and the orchestrator instead of constructing two
- `main.py` now goes through `CachedResearchService` instead of calling `ResearchOrchestrator` directly
- README's file structure diagram updated to match reality (`services/` no longer a placeholder, `test/` no longer marked "not yet implemented")

## [0.1.8] - 2026-09-07
Added:
- Unit test suite in `test/`, covering every module in `src/agents/` plus `config.py`. Uses `unittest.mock`/`monkeypatch` to fake the google-genai `Interaction`/`Usage`/step objects (`test/conftest.py`) so tests run free and fast (~0.5s, no real API calls)
- Regression tests pinning the bugs fixed in 0.1.5/0.1.7: `results_acceptable` threading `research_so_far` through to `create_plan`, `synthesis_agent` flattening research history to text, `fact_checking_agent` using `input=` (not `user_content=`) and a real model name, and `call_with_retry` catching the actual `RateLimitError` type raised by `client.interactions`
- An `xfail`-marked test documenting the known-broken `_TOOLS[tool_call.name]` tool-dispatch bug in `research_agent.py`, so it surfaces as a build failure (XPASS) once that's actually fixed rather than staying silently broken
- `[tool.pytest.ini_options]` in `pyproject.toml` pointing `testpaths` at `test/`

## [0.1.7] - 2026-09-06
Changed:
- Fixed `fact_checking_agent` calling `client.interactions.create(user_content=...)` — not a real parameter on this SDK surface; changed to `input=...` like every other call site. Only surfaced once billing was enabled and the pipeline got past the research stage for the first time
- Fixed `fact_checking_agent`'s model: `gemini-3.1-flash` does not exist (confirmed via a live `client.models.list()` call against the account) and returned a 404. Replaced with `gemini-3.6-flash`, verified live and priced the same as `gemini-3.7-flash` ($0.75/$3.75 per 1M tokens) while being newer/more capable than the (pricier, $1.50/$9.00) previous-gen `gemini-3.5-flash`
- Fixed `retry.py`'s rate-limit retry never actually engaging: `client.interactions` raises through `google.genai._gaos.lib.compat_errors.RateLimitError`, not the `google.genai.errors.ClientError` hierarchy used by other client surfaces. `call_with_retry` now catches both
- Confirmed via a real end-to-end run (~69.6k tokens, ~$0.06) that the `research_so_far` re-plan fix from 0.1.5 is working: `create_plan`'s input token count grows across loop iterations as prior research is fed back in

## [0.1.6] - 2026-08-27
Added:
- Per-stage token usage logging in `call_with_retry` (`retry.py`), so cost can be tracked per pipeline stage via the `usage` field on each interaction
- `MAX_RESEARCH_AGENT_TOOL_ROUNDS` and `RESEARCH_AGENT_MAX_OUTPUT_TOKENS` config values to bound `research_agent`'s tool-calling loop, which previously had no cap on rounds or per-call output size
- `logging.basicConfig` in `main.py` so usage/warning logs are visible when run directly

## [0.1.5] - 2026-08-27
Changed:
- Introduced `ResearchOrchestrator`, replacing the free-standing `research_process_loop`/`create_plan`/`results_acceptable` functions. It owns a single `genai.Client` for the whole research session, and that client is now passed into `research_agent`, `fact_checking_agent`, and `synthesis_agent` instead of each one constructing its own client from an API key
- Fixed `results_acceptable` not passing accumulated research history back into `create_plan` on re-plan, so the planner was re-planning with no memory of prior iterations
- Replaced the `list[tuple[AgentType, str]]` research history with a `ResearchStep` dataclass (`research_step.py`) and a shared `research_history_to_text` helper (`research_utils.py`)
- Fixed `synthesis_agent` passing the raw research history list directly as `input` to the model instead of a flattened string
- Moved the `num_iterations` cap out of a hardcoded magic number into `MAX_RESEARCH_ITERATIONS` in `config.py`
- Fixed `main.py` constructing an `Exception()` without raising it when `GEMINI_API_KEY` is missing
- Updated README's file structure section to reflect the actual repo layout instead of the earlier aspirational one

Added:
- Retry/backoff wrapper (`retry.py`) around all `client.interactions.create` calls, retrying on HTTP 429 (rate limit) responses with exponential backoff

## [0.1.4] - 2026-08-27
Changed:
- Adjusted the prompt to explicitly ask for steps for a given agent to perform

Added:

## [0.1.3] - 2026-08-26
Changed:
- Fixed type hint for tool calls list in research_agent.py
- Changed file structure to not have an extra "agentic_news" directory under "src". For now, we will have the different available services under "src"
- Adjusted all functions using the genai.Client command to take in an API key
- Set up an initial test for main.py using an api_key loaded from .env
- Commented out the "research_unwrapper" usage - we'll likely have the model innteractions handle this for us
- Adjusted the LLM calls so that the proper arguments are passed

## [0.1.2] - 2026-08-24
Changed:
- Adjusted README to fix view of file structures on github
- Created first implementation of the research agent, fact_checking agent, synthesis_agent, and the results_acceptable function
- Changed the manner we call the Language Model to Google API preferred methods

## [0.1.1] - 2026-08-23
Added:
- Added a "results_acceptable" function to have an agent determine if the results obtained sufficiently answer a research question thoroughly enough or if more research is needed. Implementation needed

Changed:
- Edited google API call function used for gemini model to be in line with online documentation
- Research process loop has been implemented. It will run other agents in order and functions as the loop the agents will run in when executing the query. Entry point to the agentic features. Max iterations included to prevent indefinite research. Currently a magic number that will be moved to the config in the future. Exception to be raised must also be further implemented (or a new exception must be created)
- Added research_agent, fact_checking_agent, and synthesis_agents have been declaration with their arguments. Implementation needed.
- AgentType enum added to distinguish agents from one another and provide a list of events that have occurred to the synthesizing agent for summarization


## [0.1.0] - 2026-08-22
- Initial Commit
- Project file structure
