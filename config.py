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

# Per-client-IP rate limit on the /api/v1/research endpoint - each request can trigger a
# multi-minute, real-money research pipeline run, so this exists to stop accidental/abusive loops.
RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "5"))
RATE_LIMIT_WINDOW_SECONDS: float = float(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# Origins allowed to call the API cross-origin (comma-separated), e.g. "https://my-frontend.com".
# Empty by default - today's frontend is served from the same origin as the API, so no
# cross-origin JS needs to read its responses. Set this only once the frontend is ever served
# from a different origin than the API (see TODO.md).
CORS_ALLOWED_ORIGINS: list[str] = [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if origin.strip()]

# "Trending" topics are derived from this app's own query history (see TrendingTopics) rather
# than an external trends source - how many of the most-asked-about topics to surface.
TRENDING_TOPICS_LIMIT: int = int(os.getenv("TRENDING_TOPICS_LIMIT", "5"))

# Free key from https://open-platform.theguardian.com/access/ - used by the search_news custom
# tool (src/agents/agent_tools/news_search_tool.py) so the research agent can pull real news
# articles with full text instead of relying only on general web search.
GUARDIAN_API_KEY: str | None = os.getenv("GUARDIAN_API_KEY")
NEWS_SEARCH_MAX_ARTICLES: int = int(os.getenv("NEWS_SEARCH_MAX_ARTICLES", "5"))
NEWS_SEARCH_MAX_BODY_CHARS: int = int(os.getenv("NEWS_SEARCH_MAX_BODY_CHARS", "3000"))

# Free key from https://newsdata.io/register - second news source, broader multi-publisher
# coverage than Guardian (used by src/agents/agent_tools/newsdata_news_tool.py). Free tier only
# returns a description/snippet, not full article body.
NEWSDATA_IO_API_KEY: str | None = os.getenv("NEWSDATA_IO_API_KEY")
NEWSDATA_MAX_ARTICLES: int = int(os.getenv("NEWSDATA_MAX_ARTICLES", "5"))

# Caps total custom (metered) tool calls - search_news + search_newsdata_news combined - across
# a whole investigation (every re-plan iteration, not just one), so one query's re-planning loop
# can't burn a disproportionate share of a free-tier daily quota on redundant searches. Distinct
# from MAX_RESEARCH_AGENT_TOOL_ROUNDS, which caps rounds, not calls - a single round can contain
# multiple tool calls. See ToolCallBudget.
MAX_NEWS_TOOL_CALLS_PER_INVESTIGATION: int = int(os.getenv("MAX_NEWS_TOOL_CALLS_PER_INVESTIGATION", "10"))
