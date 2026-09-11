from __future__ import annotations

import json
from .database import Database
from .models import ChatMessage, DiaryEntry, KnowledgeItem
from src.utils.text import fts_escape, fts_like


class DAO:
    def __init__(self):
        self.db = Database()

    async def _fts_search(self, fts_sql: str, like_sql: str, query: str,
                          limit: int, like_columns: int = 1) -> list[dict]:
        """Run an FTS5 MATCH query, falling back to LIKE when it yields nothing.

        Raw user input is escaped so MATCH syntax characters and CJK text
        (which unicode61 doesn't tokenize) still produce usable results.
        """
        like = fts_like(query)
        if not query.strip():
            return []
        try:
            match_expr = fts_escape(query)
            if match_expr:
                cursor = await self.db.connection.execute(fts_sql, (match_expr, limit))
                rows = [dict(r) for r in await cursor.fetchall()]
                if rows:
                    return rows
            cursor = await self.db.connection.execute(
                like_sql, (*[like] * like_columns, limit)
            )
            return [dict(r) for r in await cursor.fetchall()]
        except Exception:
            return []

    # --- Chat Messages ---
    async def insert_message(self, msg: ChatMessage) -> int:
        cursor = await self.db.connection.execute(
            "INSERT INTO chat_messages (platform, sender, group_name, content, msg_type, raw_data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg.platform, msg.sender, msg.group_name, msg.content, msg.msg_type, msg.raw_data),
        )
        await self.db.connection.commit()
        rowid = cursor.lastrowid
        # Keep the FTS index in sync with the base table so full-text search works.
        await self.db.connection.execute(
            "INSERT INTO messages_fts (rowid, content, sender) VALUES (?, ?, ?)",
            (rowid, msg.content, msg.sender),
        )
        await self.db.connection.commit()
        return rowid

    async def get_messages(self, platform: str = None, limit: int = 50) -> list[dict]:
        if platform:
            cursor = await self.db.connection.execute(
                "SELECT * FROM chat_messages WHERE platform = ? ORDER BY created_at DESC LIMIT ?",
                (platform, limit),
            )
        else:
            cursor = await self.db.connection.execute(
                "SELECT * FROM chat_messages ORDER BY created_at DESC LIMIT ?", (limit,)
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def search_messages(self, query: str, limit: int = 20) -> list[dict]:
        return await self._fts_search(
            "SELECT cm.* FROM chat_messages cm "
            "JOIN messages_fts mf ON cm.id = mf.rowid "
            "WHERE messages_fts MATCH ? LIMIT ?",
            "SELECT * FROM chat_messages WHERE content LIKE ? ESCAPE '\\' "
            "ORDER BY created_at DESC LIMIT ?",
            query, limit,
        )

    # --- Diary ---
    async def insert_diary(self, entry: DiaryEntry) -> int:
        tags_json = json.dumps(entry.tags, ensure_ascii=False)
        cursor = await self.db.connection.execute(
            "INSERT INTO diary_entries (content, summary, tags, mood) VALUES (?, ?, ?, ?)",
            (entry.content, entry.summary, tags_json, entry.mood),
        )
        await self.db.connection.commit()
        rowid = cursor.lastrowid
        # Keep the FTS index in sync with the base table so full-text search works.
        await self.db.connection.execute(
            "INSERT INTO diary_fts (rowid, content, summary, tags) VALUES (?, ?, ?, ?)",
            (rowid, entry.content, entry.summary, tags_json),
        )
        await self.db.connection.commit()
        return rowid

    async def get_diaries(self, limit: int = 30) -> list[dict]:
        cursor = await self.db.connection.execute(
            "SELECT * FROM diary_entries ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def search_diaries(self, query: str, limit: int = 20) -> list[dict]:
        return await self._fts_search(
            "SELECT de.* FROM diary_entries de "
            "JOIN diary_fts df ON de.id = df.rowid "
            "WHERE diary_fts MATCH ? LIMIT ?",
            "SELECT * FROM diary_entries WHERE content LIKE ? ESCAPE '\\' "
            "OR summary LIKE ? ESCAPE '\\' "
            "ORDER BY created_at DESC LIMIT ?",
            query, limit, like_columns=2,
        )

    # --- Knowledge Base ---
    async def insert_knowledge(self, item: KnowledgeItem) -> int:
        tags_json = json.dumps(item.tags, ensure_ascii=False)
        cursor = await self.db.connection.execute(
            "INSERT INTO knowledge_items (title, content, source_url, source_type, category, tags) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item.title, item.content, item.source_url, item.source_type, item.category, tags_json),
        )
        await self.db.connection.commit()
        rowid = cursor.lastrowid
        # Keep the FTS index in sync with the base table so full-text search works.
        await self.db.connection.execute(
            "INSERT INTO knowledge_fts (rowid, title, content, tags) VALUES (?, ?, ?, ?)",
            (rowid, item.title, item.content, tags_json),
        )
        await self.db.connection.commit()
        return rowid

    async def get_knowledge(self, limit: int = 30) -> list[dict]:
        cursor = await self.db.connection.execute(
            "SELECT * FROM knowledge_items ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def search_knowledge(self, query: str, limit: int = 20) -> list[dict]:
        return await self._fts_search(
            "SELECT ki.* FROM knowledge_items ki "
            "JOIN knowledge_fts kf ON ki.id = kf.rowid "
            "WHERE knowledge_fts MATCH ? LIMIT ?",
            "SELECT * FROM knowledge_items WHERE title LIKE ? ESCAPE '\\' "
            "OR content LIKE ? ESCAPE '\\' "
            "ORDER BY created_at DESC LIMIT ?",
            query, limit, like_columns=2,
        )

    # --- Chat History (AI conversation persistence) ---
    async def insert_chat_history(
        self, role: str, content: str, model: str | None = None,
        session_id: str = "default",
    ) -> int:
        """Save a single chat message to the chat_history table."""
        cursor = await self.db.connection.execute(
            "INSERT INTO chat_history (session_id, role, content, model) "
            "VALUES (?, ?, ?, ?)",
            (session_id, role, content, model),
        )
        await self.db.connection.commit()
        return cursor.lastrowid

    async def get_chat_history(
        self, limit: int = 50, session_id: str = "default",
    ) -> list[dict]:
        """Retrieve recent chat history, oldest first (for display)."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM chat_history "
            "WHERE session_id = ? "
            "ORDER BY id DESC LIMIT ?",
            (session_id, limit),
        )
        rows = await cursor.fetchall()
        # Reverse so oldest comes first (natural conversation order)
        return [dict(r) for r in reversed(rows)]

    async def clear_chat_history(self, session_id: str = "default") -> None:
        """Delete all chat history for a session."""
        await self.db.connection.execute(
            "DELETE FROM chat_history WHERE session_id = ?",
            (session_id,),
        )
        await self.db.connection.commit()
