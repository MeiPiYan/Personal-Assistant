from __future__ import annotations

import aiosqlite
from pathlib import Path


class Database:
    _instance = None
    _db: aiosqlite.Connection | None = None
    # Anchor to the project root so the DB lands in the same place regardless
    # of the process working directory.
    _db_path: str = str(Path(__file__).resolve().parents[2] / "data" / "assistant.db")
    # Vector knowledge base (P0)
    _vec_enabled: bool = False
    _vec_dim: int = 512

    def __new__(cls) -> Database:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, db_path: str | None = None,
                      vec_dim: int | None = None) -> None:
        if db_path:
            self._db_path = db_path
        if vec_dim:
            self._vec_dim = int(vec_dim)
        path = Path(self._db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = await aiosqlite.connect(str(path))
        self._db.row_factory = aiosqlite.Row
        await self._init_tables()

    async def _init_tables(self) -> None:
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                sender TEXT NOT NULL,
                group_name TEXT,
                content TEXT NOT NULL,
                msg_type TEXT DEFAULT 'text',
                raw_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                chat_identifier TEXT,
                summary TEXT NOT NULL,
                categories TEXT,
                message_count INTEGER,
                time_range_start TIMESTAMP,
                time_range_end TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS diary_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                summary TEXT,
                tags TEXT,
                mood TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS knowledge_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                source_url TEXT,
                source_type TEXT,
                category TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS structured_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                data_key TEXT NOT NULL,
                data_value TEXT NOT NULL,
                tags TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                model TEXT,
                tokens_used INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # FTS5 virtual tables
        try:
            await self._db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(title, content, tags)"
            )
        except Exception:
            pass
        try:
            await self._db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS diary_fts USING fts5(content, summary, tags)"
            )
        except Exception:
            pass
        try:
            await self._db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(content, sender)"
            )
        except Exception:
            pass

        await self._init_vector_tables()
        await self._db.commit()

    async def _init_vector_tables(self) -> None:
        """Create the knowledge-base / vector schema (P0).

        Safe on existing databases: every statement uses IF NOT EXISTS. The
        ``chunks_fts`` virtual table is the keyword channel over ``chunks``;
        ``vec_chunks`` is an optional sqlite-vec KNN index created only when the
        native extension is importable. When it is unavailable, retrieval falls
        back to a pure-python cosine scan, so the feature still works.
        """
        await self._db.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                source_path TEXT,
                source_type TEXT,
                content_hash TEXT UNIQUE,
                meta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER,
                page INTEGER,
                section TEXT,
                char_start INTEGER,
                char_end INTEGER,
                embedding BLOB,
                embedding_dim INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
            """
        )
        try:
            await self._db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts "
                "USING fts5(content, content='chunks', content_rowid='id')"
            )
        except Exception:
            pass
        self._vec_enabled = False
        try:
            import sqlite_vec  # type: ignore

            await self._db.enable_load_extension(True)
            await self._db.load_extension(sqlite_vec.loadable_path())
            await self._db.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0("
                f"chunk_id INTEGER PRIMARY KEY, embedding FLOAT[{self._vec_dim}])"
            )
            self._vec_enabled = True
        except Exception:
            self._vec_enabled = False

    @property
    def vec_enabled(self) -> bool:
        return bool(getattr(self, "_vec_enabled", False))

    @property
    def connection(self) -> aiosqlite.Connection:
        return self._db

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None
