"""Vector knowledge base service (P0).

Pipeline: structured chunking -> embedding -> storage
(``documents`` / ``chunks`` / ``chunks_fts`` / optional ``vec_chunks``) and a
retrieval entry point.

Design notes:
- Embeddings run through an ``EmbeddingBackend`` (see ``src.ai.embedding``).
- Retrieval prefers the sqlite-vec KNN index when it is enabled, and otherwise
  falls back to a pure-python cosine scan over stored chunk vectors, so the
  feature keeps working even without the native extension.
- The default backend is deterministic, offline and dependency-free (hashing),
  so P0 works with no model download and no network. Switch via the
  ``ai.embedding`` config section.
"""

from __future__ import annotations

import hashlib
import json

from src.ai.embedding import (
    EmbeddingBackend,
    cosine_similarity,
    create_embedding_backend,
)
from src.document.chunker import SemanticChunker
from src.storage.dao import DAO, _pack_vector, _unpack_vector


class VectorStore:
    """Index and search text chunks by semantic similarity."""

    def __init__(
        self,
        dao: DAO | None = None,
        backend: EmbeddingBackend | None = None,
        chunker: SemanticChunker | None = None,
    ):
        self.dao = dao or DAO()
        self._backend = backend
        self.chunker = chunker or self._build_chunker()

    # ------------------------------------------------------------------ #
    # Backend / chunker lazy init
    # ------------------------------------------------------------------ #
    @staticmethod
    def _embedding_config() -> dict:
        try:
            from src.app.config import Config

            return Config().get("ai.embedding", {}) or {}
        except Exception:
            return {}

    def _build_chunker(self) -> SemanticChunker:
        cfg = self._embedding_config()
        try:
            return SemanticChunker(
                chunk_tokens=int(cfg.get("chunk_tokens", 400) or 400),
                overlap_tokens=int(cfg.get("overlap_tokens", 60) or 60),
            )
        except Exception:
            return SemanticChunker()

    def _get_backend(self) -> EmbeddingBackend:
        if self._backend is None:
            self._backend = create_embedding_backend(self._embedding_config())
        return self._backend

    @property
    def backend(self) -> EmbeddingBackend:
        return self._get_backend()

    # ------------------------------------------------------------------ #
    # Indexing
    # ------------------------------------------------------------------ #
    async def index_text(
        self,
        text: str,
        title: str = "",
        source_path: str = "",
        source_type: str = "manual",
        meta: dict | None = None,
        dedupe: bool = True,
    ) -> dict:
        """Index a piece of text into the knowledge base.

        Returns ``{"doc_id", "chunks", "deduped"}``.
        """
        text = text or ""
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if dedupe:
            existing = await self.dao.get_document_by_hash(content_hash)
            if existing:
                return {"doc_id": existing["id"], "chunks": 0, "deduped": True}

        # Chunk *before* inserting the document, so unchunkable (effectively
        # empty) text never leaves an orphan row in ``documents``.
        pieces = self.chunker.chunk(text)
        if not pieces:
            return {"doc_id": None, "chunks": 0, "deduped": False}

        doc_id = await self.dao.insert_document(
            title=title,
            source_path=source_path,
            source_type=source_type,
            content_hash=content_hash,
            meta_json=json.dumps(meta or {}, ensure_ascii=False),
        )

        vectors = await self.backend.embed(pieces)
        chunk_rows = []
        for i, (content, vec) in enumerate(zip(pieces, vectors)):
            chunk_rows.append(
                {
                    "chunk_index": i,
                    "content": content,
                    "token_count": self.chunker.estimate_tokens(content),
                    "embedding": vec,
                }
            )
        ids = await self.dao.insert_chunks(doc_id, chunk_rows)
        return {"doc_id": doc_id, "chunks": len(ids), "deduped": False}

    async def index_knowledge_item(self, item) -> dict:
        """Index a ``KnowledgeItem`` (title + content + tags)."""
        title = getattr(item, "title", "") or ""
        content = getattr(item, "content", "") or ""
        text = f"{title}\n{content}".strip()
        meta = {
            "category": getattr(item, "category", ""),
            "tags": getattr(item, "tags", None) or [],
            "source_url": getattr(item, "source_url", ""),
        }
        return await self.index_text(
            text,
            title=title,
            source_path=getattr(item, "source_url", "") or "",
            source_type=getattr(item, "source_type", "manual") or "manual",
            meta=meta,
        )

    # ------------------------------------------------------------------ #
    # Retrieval
    # ------------------------------------------------------------------ #
    async def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Semantic search over indexed chunks.

        Returns a list of ``{"chunk_id", "doc_id", "content", "score"}`` sorted
        by descending similarity.
        """
        query = (query or "").strip()
        if not query:
            return []
        qvec = await self.backend.embed_one(query)
        if not qvec:
            return []

        if getattr(self.dao.db, "vec_enabled", False):
            try:
                return await self._search_vec(qvec, top_k)
            except Exception:
                # Fall through to the python scan on any native-index error.
                pass

        return await self._search_python(qvec, top_k)

    async def _search_vec(self, qvec: list[float], top_k: int) -> list[dict]:
        blob = _pack_vector(qvec)
        cursor = await self.dao.db.connection.execute(
            "SELECT chunk_id, distance FROM vec_chunks "
            "WHERE embedding MATCH ? AND k = ? ORDER BY distance",
            (blob, top_k),
        )
        hits = await cursor.fetchall()
        out: list[dict] = []
        for chunk_id, distance in hits:
            cur2 = await self.dao.db.connection.execute(
                "SELECT * FROM chunks WHERE id = ?", (chunk_id,)
            )
            row = await cur2.fetchone()
            if row:
                out.append(
                    {
                        "chunk_id": chunk_id,
                        "doc_id": row["doc_id"],
                        "content": row["content"],
                        "score": 1.0 / (1.0 + float(distance)),
                    }
                )
        return out

    async def _search_python(self, qvec: list[float], top_k: int) -> list[dict]:
        rows = await self.dao.get_chunks(limit=100000)
        scored: list[tuple[float, dict]] = []
        for row in rows:
            vec = _unpack_vector(row.get("embedding"))
            if not vec:
                continue
            scored.append((cosine_similarity(qvec, vec), row))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "chunk_id": row.get("id"),
                "doc_id": row.get("doc_id"),
                "content": row.get("content"),
                "score": float(score),
            }
            for score, row in scored[:top_k]
        ]
