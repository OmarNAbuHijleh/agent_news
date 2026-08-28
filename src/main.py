import logging
from .agents.research_orchestrator import ResearchOrchestrator
from config import GEMINI_API_KEY

request_to_agent: str = "Nvidia stock price"
def main():
    if not GEMINI_API_KEY:
        raise Exception()
    orchestrator = ResearchOrchestrator(GEMINI_API_KEY)
    research_results: str = orchestrator.run(request_to_agent)
    print(research_results)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    main()
