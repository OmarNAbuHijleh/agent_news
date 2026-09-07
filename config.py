# configuration for our python code. Relevant information is retrieved from our ".env" file
import os
from dotenv import load_dotenv


load_dotenv()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
MAX_RESEARCH_ITERATIONS: int = int(os.getenv("MAX_RESEARCH_ITERATIONS", "5"))
MAX_RESEARCH_AGENT_TOOL_ROUNDS: int = int(os.getenv("MAX_RESEARCH_AGENT_TOOL_ROUNDS", "6"))
RESEARCH_AGENT_MAX_OUTPUT_TOKENS: int = int(os.getenv("RESEARCH_AGENT_MAX_OUTPUT_TOKENS", "4096"))
