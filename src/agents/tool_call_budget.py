class ToolCallBudget:
    """Mutable call counter shared across every research_agent() call within a single
    investigation (all outer re-plan iterations, not just one), capping total *custom* (metered,
    e.g. news-API) tool calls. Gemini's built-in tools (google_search, url_context) aren't
    metered by us and don't count against this.

    Exists to stop one investigation's re-planning loop from making a disproportionate,
    likely-redundant number of calls to a free-tier API within a single query - a separate
    concern from the per-tool result cache (tool_result_cache.py), which stops the *same*
    search from re-hitting the API but doesn't limit genuinely distinct searches.
    """

    def __init__(self, max_calls: int):
        self._remaining = max_calls

    def try_consume(self) -> bool:
        """Returns True (and decrements the remaining budget) if a call is still allowed, False
        if the budget is already exhausted."""
        if self._remaining <= 0:
            return False
        self._remaining -= 1
        return True
