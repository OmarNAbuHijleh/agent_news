import logging
from google import genai
from collections.abc import Callable
from typing import Any
import json
from .retry import call_with_retry
from .agent_tools.news_search_tool import NEWS_SEARCH_TOOL_DECLARATION, search_news
from .agent_tools.newsdata_news_tool import NEWSDATA_NEWS_TOOL_DECLARATION, search_newsdata_news
from config import MAX_RESEARCH_AGENT_TOOL_ROUNDS, RESEARCH_AGENT_MAX_OUTPUT_TOKENS

logger = logging.getLogger(__name__)

_research_agent_prompt: str = "Given the research plan, perform tool calls in succession to execute the steps for that research plan. Cite your sources when steps are completed."

# Declarations sent to the API (tools= on interactions.create) - built-in tools (google_search,
# url_context) run server-side and never surface as function_call steps; custom tools like
# search_news/search_newsdata_news do, and need a matching entry in _TOOL_DISPATCH below to
# actually run.
_TOOL_DECLARATIONS: list[dict[str, Any]] = [
    {"type": "google_search"},
    {"type": "url_context"},
    NEWS_SEARCH_TOOL_DECLARATION,
    NEWSDATA_NEWS_TOOL_DECLARATION,
    # TODO: Consider adding the file search tool from Google.
]
# Implementations for custom tools only - looked up by name when a function_call step for a
# custom tool appears. Built-in tools are never dispatched through here.
_TOOL_DISPATCH: dict[str, Callable[..., Any]] = {
    "search_news": search_news,
    "search_newsdata_news": search_newsdata_news,
}
_GENERATION_CONFIG = {"max_output_tokens": RESEARCH_AGENT_MAX_OUTPUT_TOKENS}


def research_agent(client: genai.Client, research_plan: str) -> str:
    """Given a research plan string, we want to have our language model perform the tool calls to fulfill each research step until it completes the research.
    Bounded by MAX_RESEARCH_AGENT_TOOL_ROUNDS tool-call rounds and RESEARCH_AGENT_MAX_OUTPUT_TOKENS output tokens per call, so a single plan can't run away on token usage.
    Args:
        client <genai.Client>: The shared client for this research session
        research_plan <str>: The research plan string that will be followed, with the results provided
    Returns:
        <str>: The results of the research plan
    """
    return_text: str = ""
    # create the research agent
    interaction = call_with_retry(lambda: client.interactions.create(
        model="gemini-3.7-flash",
        system_instruction=_research_agent_prompt,
        tools=_TOOL_DECLARATIONS,
        input=research_plan,
        generation_config=_GENERATION_CONFIG,
    ), stage="research_agent.initial")

    return_text += f"{interaction.output_text}\n"

    # have the research agent make tool calls to obtain the results of each step of the research plan
    performing_research: bool = True
    tool_round: int = 0
    while performing_research:
        tool_calls = [step for step in interaction.steps if step.type=="function_call"]
        if not tool_calls:
            print(interaction.output_text)
            break
        if tool_round >= MAX_RESEARCH_AGENT_TOOL_ROUNDS:
            logger.warning("research_agent: hit MAX_RESEARCH_AGENT_TOOL_ROUNDS (%d), returning partial results", MAX_RESEARCH_AGENT_TOOL_ROUNDS)
            break
        results = []
        for tool_call in tool_calls:
            logger.info("research_agent: dispatching custom tool %s(%r)", tool_call.name, tool_call.arguments)
            tool_function = _TOOL_DISPATCH.get(tool_call.name)
            result = {"error": f"unknown tool: {tool_call.name}"} if tool_function is None else tool_function(**tool_call.arguments)
            results.append(
                {
                    "type": "function_result",
                    "name": tool_call.name,
                    "call_id": tool_call.id,
                    "result": [
                        {
                            "type": "text",
                            "text": json.dumps(result)
                        }
                    ]
                }
            )
        interaction = call_with_retry(lambda: client.interactions.create(
            model="gemini-3.7-flash",
            previous_interaction_id=interaction.id,
            input=results,
            tools=_TOOL_DECLARATIONS,
            generation_config=_GENERATION_CONFIG,
        ), stage=f"research_agent.tool_round_{tool_round}")
        return_text += f"{interaction.output_text}\n"
        tool_round += 1

    return return_text
