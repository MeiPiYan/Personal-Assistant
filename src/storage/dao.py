from __future__ import annotations

import json
from .database import Database
from .models import ChatMessage, DiaryEntry, KnowledgeItem


class DAO:
    def __init__(self):
        self.db = Database()

    # --- Chat Messages ---
    async def insert_message(self, msg: ChatMessage) -> int:
        cursor = await self.db.connection.execute(
            "INSERT INTO chat_messages (platform, sender, group_name, content, msg_type, raw_data) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (msg.platform, msg.sender, msg.group_name, msg.content, msg.msg_type, msg.raw_data),
        )
        await self.db.connection.commit()
        return cursor.lastrowid

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
        cursor = await self.db.connection.execute(
            "SELECT cm.* FROM chat_messages cm "
            "JOIN messages_fts mf ON cm.id = mf.rowid "
            "WHERE messages_fts MATCH ? LIMIT ?",
            (query, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # --- Diary ---
    async def insert_diary(self, entry: DiaryEntry) -> int:
        tags_json = json.dumps(entry.tags, ensure_ascii=False)
        cursor = await self.db.connection.execute(
            "INSERT INTO diary_entries (content, summary, tags, mood) VALUES (?, ?, ?, ?)",
            (entry.content, entry.summary, tags_json, entry.mood),
        )
        await self.db.connection.commit()
        return cursor.lastrowid

    async def get_diaries(self, limit: int = 30) -> list[dict]:
        cursor = await self.db.connection.execute(
            "SELECT * FROM diary_entries ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def search_diaries(self, query: str, limit: int = 20) -> list[dict]:
        cursor = await self.db.connection.execute(
            "SELECT de.* FROM diary_entries de "
            "JOIN diary_fts df ON de.id = df.rowid "
            "WHERE diary_fts MATCH ? LIMIT ?",
            (query, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    # --- Knowledge Base ---
    async def insert_knowledge(self, item: KnowledgeItem) -> int:
        tags_json = json.dumps(item.tags, ensure_ascii=False)
        cursor = await self.db.connection.execute(
            "INSERT INTO knowledge_items (title, content, source_url, source_type, category, tags) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item.title, item.content, item.source_url, item.source_type, item.category, tags_json),
        )
        await self.db.connection.commit()
        return cursor.lastrowid

    async def get_knowledge(self, limit: int = 30) -> list[dict]:
        cursor = await self.db.connection.execute(
            "SELECT * FROM knowledge_items ORDER BY created_at DESC LIMIT ?", (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

    async def search_knowledge(self, query: str, limit: int = 20) -> list[dict]:
        cursor = await self.db.connection.execute(
            "SELECT ki.* FROM knowledge_items ki "
            "JOIN knowledge_fts kf ON ki.id = kf.rowid "
            "WHERE knowledge_fts MATCH ? LIMIT ?",
            (query, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
