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
