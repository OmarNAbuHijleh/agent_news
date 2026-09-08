# configuration for our python code. Relevant information is retrieved from our ".env" file
import os
from dotenv import load_dotenv


load_dotenv()
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY")
MAX_RESEARCH_ITERATIONS: int = int(os.getenv("MAX_RESEARCH_ITERATIONS", "5"))
MAX_RESEARCH_AGENT_TOOL_ROUNDS: int = int(os.getenv("MAX_RESEARCH_AGENT_TOOL_ROUNDS", "6"))
RESEARCH_AGENT_MAX_OUTPUT_TOKENS: int = int(os.getenv("RESEARCH_AGENT_MAX_OUTPUT_TOKENS", "4096"))
CACHE_DB_PATH: str = os.getenv("CACHE_DB_PATH", "query_cache.sqlite3")
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", str(7 * 24 * 60 * 60)))

# Cloud cache backend (see src/services/cloud_query_cache.py) - unused until that backend is
# actually wired up in place of the local SQLite QueryCache.
CACHE_DYNAMODB_TABLE_NAME: str = os.getenv("CACHE_DYNAMODB_TABLE_NAME", "agentic-news-query-cache")
CACHE_AWS_REGION: str | None = os.getenv("CACHE_AWS_REGION")
