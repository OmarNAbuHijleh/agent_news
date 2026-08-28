from google import genai
from collections.abc import Callable
from typing import Any
import json
from .retry import call_with_retry


_research_agent_prompt: str = "Given the research plan, perform tool calls in succession to execute the steps for that research plan. Cite your sources when steps are completed."
_TOOLS: list[dict[str, str] | Callable[..., Any]]  = [
    {"type": "google_search"},
    {"type": "url_context"},
    # TODO: Consider adding the file search tool from Google. We also need to add our own custom tools once we refine agent functions and determine the flow of obtaining cached contents in databases
]


def research_agent(client: genai.Client, research_plan: str) -> str:
    """Given a research plan string, we want to have our language model perform the tool calls to fulfill each research step until it completes the research.
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
        tools=_TOOLS,
        input=research_plan,
    ))

    return_text += f"{interaction.output_text}\n"

    # have the research agent make tool calls to obtain the results of each step of the research plan
    performing_research: bool = True
    while performing_research:
        tool_calls = [step for step in interaction.steps if step.type=="function_call"]
        if not tool_calls:
            print(interaction.output_text)
            break
        results = []
        for tool_call in tool_calls:
            result = _TOOLS[tool_call.name](**tool_call.arguments)
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
            tools=_TOOLS
        ))
        return_text += f"{interaction.output_text}\n"

    return return_text
