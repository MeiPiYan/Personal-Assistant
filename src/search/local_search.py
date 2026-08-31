from __future__ import annotations

from src.storage.database import Database


class LocalSearcher:
    """SQLite FTS5 full-text search across all stored data."""

    def __init__(self):
        self.db = Database()

    async def search_messages(self, query: str, limit: int = 20) -> list[dict]:
        try:
            cursor = await self.db.connection.execute(
                "SELECT cm.* FROM chat_messages cm "
                "JOIN messages_fts mf ON cm.id = mf.rowid "
                "WHERE messages_fts MATCH ? LIMIT ?",
                (query, limit),
            )
            return [dict(r) for r in await cursor.fetchall()]
        except Exception:
            return []

    async def search_diaries(self, query: str, limit: int = 20) -> list[dict]:
        try:
            cursor = await self.db.connection.execute(
                "SELECT de.* FROM diary_entries de "
                "JOIN diary_fts df ON de.id = df.rowid "
                "WHERE diary_fts MATCH ? LIMIT ?",
                (query, limit),
            )
            return [dict(r) for r in await cursor.fetchall()]
        except Exception:
            return []

    async def search_knowledge(self, query: str, limit: int = 20) -> list[dict]:
        try:
            cursor = await self.db.connection.execute(
                "SELECT ki.* FROM knowledge_items ki "
                "JOIN knowledge_fts kf ON ki.id = kf.rowid "
                "WHERE knowledge_fts MATCH ? LIMIT ?",
                (query, limit),
            )
            return [dict(r) for r in await cursor.fetchall()]
        except Exception:
            return []

    async def search_all(self, query: str, limit: int = 10) -> dict:
        return {
            "messages": await self.search_messages(query, limit),
            "diaries": await self.search_diaries(query, limit),
            "knowledge": await self.search_knowledge(query, limit),
        }
