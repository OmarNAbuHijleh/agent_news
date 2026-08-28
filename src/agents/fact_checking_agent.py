from google import genai
from .retry import call_with_retry


_fact_checking_prompt: str = "You have been provided the results of some research. Compare and contrast the results of the research for fact-checking purposes and provide the different ideas and cited sources for each that support and go against the results"

def fact_checking_agent(client: genai.Client, research_results: str) -> str:
    """Takes in the results of the research as a string and then returns a string containing supporting and refuting evidences of the ideas presented in the research.
    Args:
        client <genai.Client>: The shared client for this research session
        research_results <str>: input research results
    Returns:
        <str>: A summary of the supporting and refuting ideas within the research and the citations
    """
    # create the research agent
    interaction = call_with_retry(lambda: client.interactions.create(
        model="gemini-3.1-flash",
        system_instruction=_fact_checking_prompt,
        user_content=research_results,
    ))
    return interaction.output_text
