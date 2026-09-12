import sqlite3
import time
from config import CACHE_DB_PATH, TRENDING_TOPICS_LIMIT


class TrendingTopics:
    """Tracks how often each normalized query has been asked, so the frontend can surface the
    most popular recent topics. This is a separate concern (and separate table) from
    QueryCache's result cache - "how often has X been asked" isn't the same thing as "what was
    the cached result for X", even though both currently live in the same SQLite file for
    convenience.
    """

    def __init__(self, db_path: str = CACHE_DB_PATH):
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS trending_topics ("
            "normalized_query TEXT PRIMARY KEY, "
            "ask_count INTEGER NOT NULL DEFAULT 0, "
            "last_asked_at REAL NOT NULL"
            ")"
        )
        self._conn.commit()

    def record_query(self, normalized_query: str) -> None:
        """Records that normalized_query was asked about just now, incrementing its count
        regardless of whether it was a cache hit or miss - popularity is about how often a
        topic is asked, not how often the pipeline actually had to run."""
        now = time.time()
        self._conn.execute(
            "INSERT INTO trending_topics (normalized_query, ask_count, last_asked_at) VALUES (?, 1, ?) "
            "ON CONFLICT(normalized_query) DO UPDATE SET ask_count = ask_count + 1, last_asked_at = excluded.last_asked_at",
            (normalized_query, now),
        )
        self._conn.commit()

    def get_top(self, limit: int = TRENDING_TOPICS_LIMIT) -> list[str]:
        """Returns up to `limit` normalized queries, most-asked first (ties broken by most
        recently asked)."""
        rows = self._conn.execute(
            "SELECT normalized_query FROM trending_topics ORDER BY ask_count DESC, last_asked_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [row[0] for row in rows]

    def close(self) -> None:
        self._conn.close()
