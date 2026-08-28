# CHANGELOG

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
