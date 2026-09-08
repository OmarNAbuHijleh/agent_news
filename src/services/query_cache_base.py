from typing import Protocol


class QueryCacheBackend(Protocol):
    """Interface shared by every query-cache backend (local SQLite, cloud DynamoDB, ...), so
    CachedResearchService can swap which one it uses without any other code changing.
    """

    def get(self, normalized_query: str) -> str | None: ...
    def set(self, normalized_query: str, result: str) -> None: ...
    def close(self) -> None: ...
