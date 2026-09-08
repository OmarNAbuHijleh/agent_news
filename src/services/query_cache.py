import sqlite3
import time
from config import CACHE_DB_PATH, CACHE_TTL_SECONDS


class QueryCache:
    """SQLite-backed cache of research results, keyed by normalized query text. Persists across
    process invocations (unlike an in-memory cache, which would never produce a hit since main.py
    runs as a fresh process each time).
    """

    def __init__(self, db_path: str = CACHE_DB_PATH, ttl_seconds: int = CACHE_TTL_SECONDS):
        self._ttl_seconds = ttl_seconds
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS query_cache ("
            "normalized_query TEXT PRIMARY KEY, "
            "result TEXT NOT NULL, "
            "created_at REAL NOT NULL"
            ")"
        )
        self._conn.commit()

    def get(self, normalized_query: str) -> str | None:
        """Returns the cached result for normalized_query, or None on a miss or an expired entry."""
        row = self._conn.execute(
            "SELECT result, created_at FROM query_cache WHERE normalized_query = ?",
            (normalized_query,),
        ).fetchone()
        if row is None:
            return None
        result, created_at = row
        if time.time() - created_at > self._ttl_seconds:
            return None
        return result

    def set(self, normalized_query: str, result: str) -> None:
        """Stores (or overwrites) the result for normalized_query, timestamped now."""
        self._conn.execute(
            "INSERT OR REPLACE INTO query_cache (normalized_query, result, created_at) VALUES (?, ?, ?)",
            (normalized_query, result, time.time()),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
