from .agent_type_enum import AgentType

_synthesis_prompt: str = "You have been given the results of research into a specific query and the research tasks performed. Synthesize the results as a short summary for delivery."

def _research_unwrapper(research_so_far: list[tuple[AgentType, str]]) -> str:
    """Helper function to unwrap a list of research tuples for passing into a language model.
    Args:
        research_so_far <list[tuple[AgentType, str]]>: A list of tuples containing the results of research performed so far.
    Returns:
        <str>: A stringified version of the research already performed for language model ingestion
    """
    ret_string: str = "### RESEARCH CYCLES ALREADY PERFORMED\n"
    for agent_type, results in research_so_far:
        ret_string += f"# {agent_type}\n{results}\n"
    return ret_string


def synthesis_agent(research_contents: list[tuple[AgentType, str]]) -> str:
    """Takes the research_contents and produces a synthesized output
    Args:
        research_contents <list<tuple<AgentType, str>>>: A list of research plans, results, and fact-checkings
    Returns:
        <str>: A summary of all of the results
    """
    client = genai.Client()
    response = client.interactions.create(
        model="gemini-3.1-flash-lite",
        config={
            "system_instruction": _synthesis_prompt
        },
        contents=f"{_research_unwrapper(research_contents)}"
    )

    return response.output_text
