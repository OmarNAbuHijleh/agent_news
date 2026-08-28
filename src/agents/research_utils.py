from .research_step import ResearchStep


def research_history_to_text(research_so_far: list[ResearchStep]) -> str:
    """Flattens accumulated research steps into a single text block for language model input.
    Args:
        research_so_far <list[ResearchStep]>: The steps performed so far in the research session
    Returns:
        <str>: A stringified version of the research already performed, for language model ingestion
    """
    ret_string: str = "### RESEARCH CYCLES ALREADY PERFORMED\n"
    for step in research_so_far:
        ret_string += f"# {step.agent_type.value}\n{step.content}\n"
    return ret_string
