# this will be where we have the LLM perform research planning. It will receive the user query and determine the steps it wants to take to perform the research
from google import genai
from .research_agent import research_agent
from .fact_checking_agent import fact_checking_agent
from .synthesis_agent import synthesis_agent
from .agent_type_enum import AgentType

_research_agent_system_prompt: str = """You are a researcher that is creating a research plan for the news relating to the user query."""


def create_plan(user_input_query: str) -> str:
    """Given a user input query, a research plan will be created. Following the creation of the plan, the plan will be executed in a loop until the plan is deemed completed by the planner.
    Args:
        user_input_query <str>: The user query as a string
    Returns:
        <str> | <None>: The research plan developed for answering the user query. <None> result if it failed to create a research plan
    """
    # TODO: Consider using a different model with the thinking configuration set
    client = genai.Client()
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        config={
            "system_instruction": _research_agent_system_prompt
        },
        contents=f"{user_input_query}"
    )
    research_plan = response.text # TODO: Handle the "None" case later
    if not research_plan:
        return ""
    return research_plan


def results_acceptable(research_results: str, fact_checking_results: str) -> tuple[bool, str]:

    return False, ""


def research_process_loop(user_input_query: str) -> str:
    """
        Loop that runs when our API receives a user query. The user query will first be used to develop a plan, followed by a research agent run to answer the query. Following the research agent run, the results of the run are fact-checked by an agent and then the results are compiled and delivered by another agent when the language model determines the results are satisfactory.
        Args:
            user_input_query <str>: The query used to produce our test plan
        Returns:
            A string containing the synthesized results of our research.
    """
    # TODO: Add a path to see if we've properly researched the topic already and what other information we may or may not need. If we have not sufficiently researched this topic, we'll want to run the entire research agent pipeline
    research_contents: list[tuple[AgentType, str]] = []
    research_not_completed: bool = True
    research_plan: str = create_plan(user_input_query)
    num_iterations: int = 0
    while research_not_completed:
        if num_iterations >= 5: # TODO: Add the number 60 to the config file. Work out the details of the exception here.
            raise Exception() # we've hit our max number of iterations and will no longer answer this query
        research_contents.append((AgentType.RESEARCH_PLANNER, research_plan))
        # run the research process
        research_results = research_agent(research_plan)
        fact_checking_results = fact_checking_agent(research_results)

        research_not_completed, research_plan = results_acceptable(research_results, fact_checking_results) #this will determine if the results are acceptable and research is completed. If it is not, create a new research plan and then the cycle will continue

        num_iterations += 1

    synthesized_results: str = synthesis_agent(research_contents)
    return synthesized_results
