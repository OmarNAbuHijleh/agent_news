import logging
from .services.cached_research_service import CachedResearchService
from config import GEMINI_API_KEY

request_to_agent: str = "Nvidia stock price"
def main():
    if not GEMINI_API_KEY:
        raise Exception()
    service = CachedResearchService(GEMINI_API_KEY)
    research_results: str = service.run(request_to_agent)
    print(research_results)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    main()
