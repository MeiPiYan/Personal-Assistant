"""Hybrid retrieval: BM25 (FTS5) + dense vector, fused with RRF (P2).

Why hybrid: keyword search wins on proper nouns, numbers and rare terms, while
dense retrieval wins on paraphrase / synonym / cross-lingual intent. Neither is
strictly better, so we run both and merge with Reciprocal Rank Fusion:

    score(d) = Σ_i  1 / (k + rank_i(d))

RRF only needs ranks (not comparable scores), which makes it robust across two
very different scorers. Optional reranking can be layered on top later.
"""

from __future__ import annotations

from src.search.vector_search import VectorStore


def rrf_fuse(
    ranked_lists: list[list[dict]],
    k: int = 60,
    top_k: int = 10,
    key: str = "chunk_id",
) -> list[dict]:
    """Fuse several ranked result lists with Reciprocal Rank Fusion.

    Each input list is ordered best-first. Items are identified by ``key``.
    Returns the fused top-k, each annotated with ``rrf_score`` and ``sources``.
    """
    fused: dict[object, dict] = {}
    for list_index, ranked in enumerate(ranked_lists):
        for rank, item in enumerate(ranked):
            ident = item.get(key)
            if ident is None:
                # Fall back to content so unkeyed items still participate.
                ident = ("content", item.get("content", ""))
            contribution = 1.0 / (k + rank + 1)
            entry = fused.get(ident)
            if entry is None:
                entry = dict(item)
                entry["rrf_score"] = 0.0
                entry["sources"] = []
                fused[ident] = entry
            entry["rrf_score"] += contribution
            if list_index not in entry["sources"]:
                entry["sources"].append(list_index)
    ordered = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)
    return ordered[:top_k]


class HybridSearcher:
    """Fuse lexical (DAOMixin FTS) and semantic (VectorStore) retrieval."""

    def __init__(self, dao=None, vector_store: VectorStore | None = None):
        self.vector_store = vector_store or VectorStore(dao=dao)

    @property
    def dao(self):
        return self.vector_store.dao

    async def search(
        self,
        query: str,
        top_k: int = 10,
        candidate_k: int = 20,
        k: int = 60,
    ) -> list[dict]:
        """Return fused results for ``query``.

        Each item: ``{"chunk_id", "doc_id", "content", "score", "rrf_score",
        "sources"}`` where ``sources`` is a list of channel indexes
        (0 = lexical/BM25, 1 = vector).
        """
        query = (query or "").strip()
        if not query:
            return []

        lexical = await self._lexical(query, candidate_k)
        semantic = await self._semantic(query, candidate_k)

        fused = rrf_fuse([lexical, semantic], k=k, top_k=top_k)
        for item in fused:
            item["score"] = item.get("rrf_score", 0.0)
        return fused

    async def _lexical(self, query: str, limit: int) -> list[dict]:
        try:
            rows = await self.dao.search_chunks_fts(query, limit=limit)
        except Exception as e:
            print(f"[HybridSearcher] lexical search failed: {e}")
            return []
        out = []
        for r in rows:
            out.append(
                {
                    "chunk_id": r.get("id"),
                    "doc_id": r.get("doc_id"),
                    "content": r.get("content", ""),
                }
            )
        return out

    async def _semantic(self, query: str, limit: int) -> list[dict]:
        try:
            rows = await self.vector_store.search(query, top_k=limit)
        except Exception as e:
            print(f"[HybridSearcher] semantic search failed: {e}")
            return []
        return [
            {
                "chunk_id": r.get("chunk_id"),
                "doc_id": r.get("doc_id"),
                "content": r.get("content", ""),
            }
            for r in rows
        ]

    async def build_context(
        self, query: str, top_k: int = 5, max_chars: int = 2000
    ) -> tuple[str, list[dict]]:
        """Return ``(context_text, sources)`` ready to inject into a prompt."""
        hits = await self.search(query, top_k=top_k)
        if not hits:
            return "", []
        parts: list[str] = []
        used = 0
        sources: list[dict] = []
        for i, h in enumerate(hits, start=1):
            content = (h.get("content") or "").strip()
            if not content:
                continue
            block = f"[{i}] {content}"
            if used + len(block) > max_chars:
                break
            parts.append(block)
            used += len(block)
            sources.append(h)
        return "\n\n".join(parts), sources
