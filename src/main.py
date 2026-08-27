from .agents import research_orchestrator
from config import GEMINI_API_KEY

request_to_agent: str = "Nvidia stock price"
def main():
    if not GEMINI_API_KEY:
        Exception()
    research_results: str = research_orchestrator.research_process_loop(request_to_agent, GEMINI_API_KEY)
    print(research_results)

if __name__ == "__main__":
    main()
