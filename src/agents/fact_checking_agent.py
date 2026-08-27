from google import genai


_fact_checking_prompt: str = "You have been provided the results of some research. Compare and contrast the results of the research for fact-checking purposes and provide the different ideas and cited sources for each that support and go against the results"

def fact_checking_agent(research_results: str, api_key: str) -> str:
    """Takes in the results of the research as a string and then returns a string containing supporting and refuting evidences of the ideas presented in the research.
    Args:
        research_results <str>: input research results
    Returns:
        <str>: A summary of the supporting and refuting ideas within the research and the citations
    """
    client = genai.Client(api_key=api_key)
    # create the research agent
    interaction = client.interactions.create(
        model="gemini-3.1-flash",
        system_instruction=_fact_checking_prompt,
        user_content=research_results,
    )
    return interaction.output_text
