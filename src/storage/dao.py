from __future__ import annotations

import json
import struct
from .database import Database
from .models import ChatMessage, DiaryEntry, KnowledgeItem
from src.utils.text import fts_escape, fts_like


def _pack_vector(vec: list[float]) -> bytes:
    """Pack a float list into float32 bytes (BLOB / sqlite-vec storage)."""
    return struct.pack(f"<{len(vec)}f", *[float(x) for x in vec])


def _unpack_vector(blob: bytes | None) -> list[float]:
    """Unpack float32 bytes back into a float list."""
    if not blob:
        return []
    count = len(blob) // 4
    return list(struct.unpack(f"<{count}f", blob[: count * 4]))


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

    # --- Knowledge base: documents & chunks (P0 vector KB) ---
    async def get_document_by_hash(self, content_hash: str) -> dict | None:
        cursor = await self.db.connection.execute(
            "SELECT * FROM documents WHERE content_hash = ?", (content_hash,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_document(self, doc_id: int) -> dict | None:
        cursor = await self.db.connection.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def insert_document(self, title: str, source_path: str,
                              source_type: str, content_hash: str,
                              meta_json: str = "{}") -> int:
        cursor = await self.db.connection.execute(
            "INSERT INTO documents (title, source_path, source_type, "
            "content_hash, meta) VALUES (?, ?, ?, ?, ?)",
            (title, source_path, source_type, content_hash, meta_json),
        )
        await self.db.connection.commit()
        return cursor.lastrowid

    async def insert_chunks(self, doc_id: int, chunks: list[dict]) -> list[int]:
        """Insert chunks and sync both the keyword (FTS) and vector indexes.

        Each item may contain: content, chunk_index, token_count, page, section,
        char_start, char_end, embedding (list[float] | None).
        """
        ids: list[int] = []
        conn = self.db.connection
        for i, ch in enumerate(chunks):
            emb = ch.get("embedding")
            blob = _pack_vector(emb) if emb else None
            dim = len(emb) if emb else None
            cursor = await conn.execute(
                "INSERT INTO chunks (doc_id, chunk_index, content, token_count, "
                "page, section, char_start, char_end, embedding, embedding_dim) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    doc_id,
                    ch.get("chunk_index", i),
                    ch.get("content", ""),
                    ch.get("token_count"),
                    ch.get("page"),
                    ch.get("section"),
                    ch.get("char_start"),
                    ch.get("char_end"),
                    blob,
                    dim,
                ),
            )
            rowid = cursor.lastrowid
            ids.append(rowid)
            # Keep the FTS keyword channel in sync (historical bug: forgot this).
            await conn.execute(
                "INSERT INTO chunks_fts (rowid, content) VALUES (?, ?)",
                (rowid, ch.get("content", "")),
            )
            # Keep the optional sqlite-vec index in sync.
            if emb and getattr(self.db, "vec_enabled", False):
                await conn.execute(
                    "INSERT INTO vec_chunks (chunk_id, embedding) VALUES (?, ?)",
                    (rowid, _pack_vector(emb)),
                )
        await conn.commit()
        return ids

    async def get_chunk(self, chunk_id: int) -> dict | None:
        """Point query for a single chunk by primary key (graph nodes)."""
        cursor = await self.db.connection.execute(
            "SELECT * FROM chunks WHERE id = ?", (chunk_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def get_chunks(self, doc_id: int | None = None,
                         limit: int = 5000) -> list[dict]:
        if doc_id is not None:
            cursor = await self.db.connection.execute(
                "SELECT * FROM chunks WHERE doc_id = ? ORDER BY chunk_index LIMIT ?",
                (doc_id, limit),
            )
        else:
            cursor = await self.db.connection.execute(
                "SELECT * FROM chunks ORDER BY id LIMIT ?", (limit,)
            )
        return [dict(r) for r in await cursor.fetchall()]

    async def count_chunks(self, doc_id: int | None = None) -> int:
        if doc_id is not None:
            cursor = await self.db.connection.execute(
                "SELECT COUNT(*) FROM chunks WHERE doc_id = ?", (doc_id,)
            )
        else:
            cursor = await self.db.connection.execute("SELECT COUNT(*) FROM chunks")
        row = await cursor.fetchone()
        return int(row[0]) if row else 0

    async def delete_document(self, doc_id: int) -> None:
        conn = self.db.connection
        cursor = await conn.execute(
            "SELECT id FROM chunks WHERE doc_id = ?", (doc_id,)
        )
        chunk_ids = [r[0] for r in await cursor.fetchall()]
        for cid in chunk_ids:
            try:
                await conn.execute("DELETE FROM chunks_fts WHERE rowid = ?", (cid,))
            except Exception:
                pass
            if getattr(self.db, "vec_enabled", False):
                try:
                    await conn.execute(
                        "DELETE FROM vec_chunks WHERE chunk_id = ?", (cid,)
                    )
                except Exception:
                    pass
        await conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
        await conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        await conn.commit()

    async def search_chunks_fts(self, query: str, limit: int = 20) -> list[dict]:
        return await self._fts_search(
            "SELECT c.* FROM chunks c JOIN chunks_fts f ON c.id = f.rowid "
            "WHERE chunks_fts MATCH ? LIMIT ?",
            "SELECT * FROM chunks WHERE content LIKE ? ESCAPE '\\' LIMIT ?",
            query, limit,
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
