from __future__ import annotations

import re


def truncate(text: str, max_len: int = 200) -> str:
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


def extract_urls(text: str) -> list[str]:
    pattern = r'https?://[^\s<>"\')\]]+'
    return re.findall(pattern, text)


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def fts_escape(query: str) -> str:
    """Turn raw user input into a safe FTS5 MATCH expression.

    Each whitespace-separated term is double-quoted (internal quotes doubled)
    so FTS5 syntax characters like " - * ( ) can't trigger errors. Terms are
    joined with spaces, which FTS5 treats as implicit AND.
    """
    terms = [t for t in query.split() if t]
    if not terms:
        return ""
    return " ".join('"' + t.replace('"', '""') + '"' for t in terms)


def fts_like(query: str) -> str:
    """Escape user input for a LIKE '%...%' pattern (wildcards neutralized)."""
    escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"
