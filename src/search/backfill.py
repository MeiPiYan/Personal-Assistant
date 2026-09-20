"""Backfill service: index pre-existing records into the vector knowledge base (P1).

P0 wired new knowledge entry / document ingestion to the vector store. P1 adds a
one-time (and re-runnable) backfill for data that already existed before the
vector feature landed, plus the indexing hooks used by document ingestion.

The service is deliberately defensive:
- idempotent (content-hash dedupe in ``VectorStore``), so re-running is safe
- per-item retry with a bounded attempt count
- progress callback for the UI
- never raises on a single item; failures are counted and reported
"""

from __future__ import annotations

import asyncio

from src.search.vector_search import VectorStore


class BackfillService:
    def __init__(self, dao=None, vector_store: VectorStore | None = None):
        self.vector_store = vector_store or VectorStore(dao=dao)

    # ------------------------------------------------------------------ #
    # Knowledge items
    # ------------------------------------------------------------------ #
    async def backfill_knowledge(
        self,
        batch_size: int = 50,
        retries: int = 2,
        on_progress=None,
    ) -> dict:
        """Index all existing ``knowledge_items`` into the vector KB.

        Returns ``{"total", "indexed", "deduped", "failed"}``.
        """
        dao = self.vector_store.dao
        items = await dao.get_knowledge(limit=1_000_000)
        total = len(items)
        indexed = 0
        deduped = 0
        failed = 0

        for i, row in enumerate(items):
            ok = await self._index_one(self._row_to_item(row), retries=retries)
            if ok is None:
                failed += 1
            elif ok:
                indexed += 1
            else:
                deduped += 1

            if on_progress and ((i + 1) % batch_size == 0 or i + 1 == total):
                try:
                    on_progress(i + 1, total)
                except Exception:
                    pass
            # Yield to the loop between batches so the UI stays responsive.
            if (i + 1) % batch_size == 0:
                await asyncio.sleep(0)

        return {
            "total": total,
            "indexed": indexed,
            "deduped": deduped,
            "failed": failed,
        }

    # ------------------------------------------------------------------ #
    # Diaries
    # ------------------------------------------------------------------ #
    async def backfill_diaries(
        self,
        batch_size: int = 50,
        retries: int = 2,
        on_progress=None,
    ) -> dict:
        """Index existing ``diary_entries`` into the vector KB."""
        dao = self.vector_store.dao
        rows = await dao.get_diaries(limit=1_000_000)
        total = len(rows)
        indexed = deduped = failed = 0

        for i, row in enumerate(rows):
            content = (row.get("content") or "").strip()
            if not content:
                continue
            ok = await self._index_one_raw(
                content,
                title=f"日记 {str(row.get('created_at', ''))[:10]}",
                source_type="diary",
                retries=retries,
            )
            if ok is None:
                failed += 1
            elif ok:
                indexed += 1
            else:
                deduped += 1
            if on_progress and ((i + 1) % batch_size == 0 or i + 1 == total):
                try:
                    on_progress(i + 1, total)
                except Exception:
                    pass
            if (i + 1) % batch_size == 0:
                await asyncio.sleep(0)

        return {"total": total, "indexed": indexed, "deduped": deduped, "failed": failed}

    async def backfill_all(self, **kwargs) -> dict:
        """Convenience: backfill knowledge and diaries together."""
        k = await self.backfill_knowledge(**kwargs)
        d = await self.backfill_diaries(**kwargs)
        return {"knowledge": k, "diary": d}

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    @staticmethod
    def _row_to_item(row: dict):
        from src.storage.models import KnowledgeItem

        tags = row.get("tags")
        if isinstance(tags, str):
            import json

            try:
                tags = json.loads(tags)
            except Exception:
                tags = [t.strip() for t in tags.split(",") if t.strip()]
        return KnowledgeItem(
            title=row.get("title") or "",
            content=row.get("content") or "",
            source_url=row.get("source_url") or "",
            source_type=row.get("source_type") or "manual",
            category=row.get("category") or "",
            tags=tags or [],
        )

    async def _index_one(self, item, retries: int = 2):
        """Return True if indexed, False if deduped, None if failed."""
        last_exc = None
        for _ in range(retries + 1):
            try:
                res = await self.vector_store.index_knowledge_item(item)
                if res.get("deduped"):
                    return False
                # chunks==0 without dedupe means the text could not be chunked;
                # report it as failed instead of mis-counting it as deduped.
                return True if res.get("chunks", 0) > 0 else None
            except Exception as e:  # noqa: BLE001
                last_exc = e
                await asyncio.sleep(0.05)
        return None if last_exc else False

    async def _index_one_raw(self, text, title, source_type, retries: int = 2):
        last_exc = None
        for _ in range(retries + 1):
            try:
                res = await self.vector_store.index_text(
                    text, title=title, source_type=source_type
                )
                if res.get("deduped"):
                    return False
                return True if res.get("chunks", 0) > 0 else None
            except Exception as e:  # noqa: BLE001
                last_exc = e
                await asyncio.sleep(0.05)
        return None if last_exc else False
