from google import genai
from .research_step import ResearchStep
from .research_utils import research_history_to_text
from .retry import call_with_retry

_synthesis_prompt: str = "You have been given the results of research into a specific query and the research tasks performed. Synthesize the results as a short summary for delivery."


def synthesis_agent(client: genai.Client, research_contents: list[ResearchStep]) -> str:
    """Takes the research_contents and produces a synthesized output
    Args:
        client <genai.Client>: The shared client for this research session
        research_contents <list[ResearchStep]>: The research plans, results, and fact-checkings performed
    Returns:
        <str>: A summary of all of the results
    """
    response = call_with_retry(lambda: client.interactions.create(
        model="gemini-3.1-flash-lite",
        system_instruction=_synthesis_prompt,
        input=research_history_to_text(research_contents)
    ), stage="synthesis_agent")

    return response.output_text
