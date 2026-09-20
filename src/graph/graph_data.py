"""Graph data provider: level-1 candidates + keyword labels (plan §6, §8.2).

Read-only on top of DAO / chunks table. sqlite-vec KNN is used when
available; otherwise a pure-python cosine fallback over chunks.embedding.
"""

from __future__ import annotations

import math
import re
from collections import Counter

# Common Chinese/English stopwords for label extraction (small offline set)
_STOPWORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看",
    "好", "自己", "这", "那", "与", "及", "或", "the", "a", "an", "of", "to",
    "in", "is", "are", "and", "or", "for", "on", "it", "this", "that",
}


def extract_label(content: str, max_chars: int = 12) -> str:
    """Extract a short keyword/phrase label from chunk content.

    Offline TF heuristic: pick highest-frequency non-stopword token; CJK text
    is split on punctuation/whitespace into short phrases, ASCII on spaces.
    Falls back to the head of the content, then to a placeholder.
    """
    text = (content or "").strip()
    if not text:
        return "（空）"
    # candidate tokens: CJK runs up to 6 chars, or ascii words
    tokens = re.findall(r"[\u4e00-\u9fff]{1,6}|[A-Za-z0-9_]{2,}", text)
    tokens = [t for t in tokens if t.lower() not in _STOPWORDS]
    if tokens:
        counts = Counter(tokens)
        best = max(counts.items(), key=lambda kv: (kv[1], len(kv[0])))[0]
    else:
        best = text[:max_chars]
    label = best.strip()
    if len(label) > max_chars:
        label = label[: max_chars - 1] + "…"
    return label or text[:max_chars] or "（空）"


def _cosine(a: list[float], b: list[float]) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = math.sqrt(sum(x * x for x in a))
    db = math.sqrt(sum(y * y for y in b))
    if da == 0 or db == 0:
        return 0.0
    return num / (da * db)


class GraphDataProvider:
    """Provides node metadata and level-1 related candidates."""

    def __init__(self, dao, top_k: int = 8, threshold: float = 0.35):
        self.dao = dao
        self.top_k = top_k
        self.threshold = threshold

    # ------------------------------------------------------------------
    async def get_node(self, chunk_id: int) -> dict | None:
        """Return node metadata {id, doc_id, content, label} or None."""
        rows = await self.dao.get_chunks(limit=100000)
        for r in rows:
            if r.get("id") == chunk_id:
                out = dict(r)
                out["label"] = extract_label(out.get("content", ""))
                return out
        return None

    async def related_chunks(self, chunk_id: int) -> list[dict]:
        """Level-1 candidates for a chunk: cosine >= threshold, top-k.

        Each result: {chunk_id, doc_id, content, score}.
        """
        rows = await self.dao.get_chunks(limit=100000)
        target = None
        for r in rows:
            if r.get("id") == chunk_id:
                target = r
                break
        if target is None:
            return []

        tvec = _to_vec(target.get("embedding"))
        if tvec is None:
            return []

        scored: list[dict] = []
        for r in rows:
            if r.get("id") == chunk_id:
                continue
            vec = _to_vec(r.get("embedding"))
            if vec is None:
                continue
            score = _cosine(tvec, vec)
            if score >= self.threshold:
                scored.append(
                    {
                        "chunk_id": r["id"],
                        "doc_id": r.get("doc_id"),
                        "content": r.get("content", ""),
                        "score": round(score, 4),
                    }
                )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[: self.top_k]

    async def related_ids(self, chunk_id: int) -> list[int]:
        """Convenience wrapper for the state machine provider hook."""
        return [c["chunk_id"] for c in await self.related_chunks(chunk_id)]


def _to_vec(blob) -> list[float] | None:
    """Decode an embedding stored as BLOB (float32) into a python list."""
    if blob is None:
        return None
    import struct

    if isinstance(blob, (bytes, bytearray)):
        n = len(blob) // 4
        if n == 0:
            return None
        return list(struct.unpack(f"<{n}f", bytes(blob)))
    if isinstance(blob, (list, tuple)):
        return list(blob)
    return None
