# this will be where we have the LLM perform research planning. It will receive the user query and determine the steps it wants to take to perform the research
from google import genai
from .research_agent import research_agent
from .fact_checking_agent import fact_checking_agent
from .synthesis_agent import synthesis_agent
from .agent_type_enum import AgentType
from .research_step import ResearchStep
from .research_utils import research_history_to_text
from .retry import call_with_retry
from config import MAX_RESEARCH_ITERATIONS


_research_agent_system_prompt: str = """You are a researcher that is creating a research plan for the news relating to the user query. Produce a list of steps as tasks to perform to answer the query with proper research. Output the steps as so (replacing the '<>' with actual step):
1.) <Step 1 contents>
2.) <Step 2 contents>
etc.
"""
_results_satisfied_check_prompt: str = """You have been given a query, the results of some research into that query, and a fact-checking summary of the research accepting or refuting the results. Determine if the results and fact checking satisfies the query. If so, responsd with only the word 'SATISFIED'. Otherwise, only respond with the word 'UNSATISFIED'"""


class ResearchOrchestrator:
    """Runs the plan -> research -> fact-check -> synthesize loop for a single research session.

    One instance holds one genai.Client, reused across every stage and every loop iteration for
    that session, so a caller serving multiple users can keep one orchestrator (and one client)
    per user/session instead of spinning up a new client on every agent call.
    """

    def __init__(self, api_key: str):
        self._client = genai.Client(api_key=api_key)

    def create_plan(self, user_input_query: str, research_so_far: list[ResearchStep] | None = None) -> str:
        """Given a user input query, a research plan will be created. Following the creation of the plan, the plan will be executed in a loop until the plan is deemed completed by the planner.
        Args:
            user_input_query <str>: The user query as a string
            research_so_far <list[ResearchStep] | None> = None: The research performed so far, if this is a re-plan partway through a session. Default is None
        Returns:
            <str>: The research plan developed for answering the user query. Empty string if it failed to create a research plan
        """
        # TODO: Consider using a different model with the thinking configuration set
        contents_for_model = user_input_query if not research_so_far else f"{user_input_query}\n{research_history_to_text(research_so_far)}"

        response = call_with_retry(lambda: self._client.interactions.create(
            model="gemini-3.1-flash-lite",
            input=contents_for_model,
            system_instruction=_research_agent_system_prompt
        ))
        return response.output_text or "" # TODO: Handle the "None" case later

    def results_acceptable(self, research_results: str, fact_checking_results: str, user_input_query: str, research_so_far: list[ResearchStep]) -> tuple[bool, str]:
        """Given the research results and the fact checker results, we'll determine if the results sufficiently answer the query.
        Args:
            research_results <str>: The results of our research
            fact_checking_results <str>: The results of our fact-checker
            user_input_query <str>: The original user query
            research_so_far <list[ResearchStep]>: The research performed so far this session, passed through to a re-plan if the results are not acceptable
        Returns:
            <bool>: False if the research and fact checking is sufficent. True if not, and a new research plan is created
            <str>: The new research plan if the results are not acceptable
        """
        contents_for_model = f"User Input Query: {user_input_query}\nResearch Results: {research_results}\nFact Checking Results: {fact_checking_results}"
        response = call_with_retry(lambda: self._client.interactions.create(
            input=contents_for_model,
            model="gemini-3.1-flash-lite",
            system_instruction=_results_satisfied_check_prompt
        ))
        if response.output_text == "SATISFIED":
            return False, ""
        elif response.output_text == "UNSATISFIED":
            return True, self.create_plan(user_input_query, research_so_far=research_so_far)
        else:
            raise Exception() # TODO: Check for cases where this is the result

    def run(self, user_input_query: str) -> str:
        """Runs when our API receives a user query. The user query will first be used to develop a plan, followed by a research agent run to answer the query. Following the research agent run, the results of the run are fact-checked by an agent and then the results are compiled and delivered by another agent when the language model determines the results are satisfactory.
        Args:
            user_input_query <str>: The query used to produce our research plan
        Returns:
            A string containing the synthesized results of our research.
        """
        # TODO: Add a path to see if we've properly researched the topic already and what other information we may or may not need. If we have not sufficiently researched this topic, we'll want to run the entire research agent pipeline

        research_contents: list[ResearchStep] = [] # This will be used to track our research process to see what we've already done and the results
        research_not_completed: bool = True
        research_plan: str = self.create_plan(user_input_query)
        num_iterations: int = 0
        while research_not_completed:
            # we've hit our max number of iterations and will no longer answer this query
            if num_iterations >= MAX_RESEARCH_ITERATIONS: # TODO: Work out the details of the exception here.
                raise Exception()

            research_contents.append(ResearchStep(AgentType.RESEARCH_PLANNER, research_plan))
            # run the research process
            research_results = research_agent(self._client, research_plan)
            research_contents.append(ResearchStep(AgentType.RESEARCHER, research_results))
            fact_checking_results = fact_checking_agent(self._client, research_results)
            research_contents.append(ResearchStep(AgentType.FACT_CHECKING, fact_checking_results))

            research_not_completed, research_plan = self.results_acceptable(research_results, fact_checking_results, user_input_query, research_contents) #this will determine if the results are acceptable and research is completed. If it is not, create a new research plan and then the cycle will continue
            num_iterations += 1

        return synthesis_agent(self._client, research_contents)
