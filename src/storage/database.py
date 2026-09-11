from __future__ import annotations

import aiosqlite
from pathlib import Path


class Database:
    _instance = None
    _db: aiosqlite.Connection | None = None
    # Anchor to the project root so the DB lands in the same place regardless
    # of the process working directory.
    _db_path: str = str(Path(__file__).resolve().parents[2] / "data" / "assistant.db")

    def __new__(cls) -> Database:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self, db_path: str | None = None) -> None:
        if db_path:
            self._db_path = db_path
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

        await self._db.commit()

    @property
    def connection(self) -> aiosqlite.Connection:
        return self._db

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None
