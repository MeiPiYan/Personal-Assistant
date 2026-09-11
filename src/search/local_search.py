from __future__ import annotations

from src.storage.database import Database
from src.utils.text import fts_escape, fts_like


class LocalSearcher:
    """SQLite FTS5 full-text search across all stored data.

    FTS5's default tokenizer does not split CJK text into sub-tokens, and raw
    user input can contain MATCH syntax characters, so queries are escaped and
    empty results fall back to a LIKE substring scan on the base table.
    """

    def __init__(self):
        self.db = Database()

    async def _fts(self, sql: str, query: str, limit: int) -> list[dict]:
        match_expr = fts_escape(query)
        if not match_expr:
            return []
        try:
            cursor = await self.db.connection.execute(sql, (match_expr, limit))
            return [dict(r) for r in await cursor.fetchall()]
        except Exception:
            return []

    async def _like(self, sql: str, query: str, limit: int, columns: int = 1) -> list[dict]:
        like = fts_like(query)
        if not query.strip():
            return []
        try:
            cursor = await self.db.connection.execute(sql, (*[like] * columns, limit))
            return [dict(r) for r in await cursor.fetchall()]
        except Exception:
            return []

    async def search_messages(self, query: str, limit: int = 20) -> list[dict]:
        rows = await self._fts(
            "SELECT cm.* FROM chat_messages cm "
            "JOIN messages_fts mf ON cm.id = mf.rowid "
            "WHERE messages_fts MATCH ? LIMIT ?",
            query, limit,
        )
        if not rows:
            rows = await self._like(
                "SELECT * FROM chat_messages WHERE content LIKE ? ESCAPE '\\' "
                "ORDER BY created_at DESC LIMIT ?",
                query, limit,
            )
        return rows

    async def search_diaries(self, query: str, limit: int = 20) -> list[dict]:
        rows = await self._fts(
            "SELECT de.* FROM diary_entries de "
            "JOIN diary_fts df ON de.id = df.rowid "
            "WHERE diary_fts MATCH ? LIMIT ?",
            query, limit,
        )
        if not rows:
            rows = await self._like(
                "SELECT * FROM diary_entries WHERE content LIKE ? ESCAPE '\\' "
                "OR summary LIKE ? ESCAPE '\\' "
                "ORDER BY created_at DESC LIMIT ?",
                query, limit, columns=2,
            )
        return rows

    async def search_knowledge(self, query: str, limit: int = 20) -> list[dict]:
        rows = await self._fts(
            "SELECT ki.* FROM knowledge_items ki "
            "JOIN knowledge_fts kf ON ki.id = kf.rowid "
            "WHERE knowledge_fts MATCH ? LIMIT ?",
            query, limit,
        )
        if not rows:
            rows = await self._like(
                "SELECT * FROM knowledge_items WHERE title LIKE ? ESCAPE '\\' "
                "OR content LIKE ? ESCAPE '\\' "
                "ORDER BY created_at DESC LIMIT ?",
                query, limit, columns=2,
            )
        return rows

    async def search_all(self, query: str, limit: int = 10) -> dict:
        return {
            "messages": await self.search_messages(query, limit),
            "diaries": await self.search_diaries(query, limit),
            "knowledge": await self.search_knowledge(query, limit),
        }
