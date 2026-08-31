from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ChatMessage:
    platform: str
    sender: str
    content: str
    group_name: str = ""
    msg_type: str = "text"
    raw_data: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChatSummary:
    platform: str
    chat_identifier: str
    summary: str
    categories: dict = field(default_factory=dict)
    message_count: int = 0
    time_range_start: datetime | None = None
    time_range_end: datetime | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class DiaryEntry:
    content: str
    summary: str = ""
    tags: list[str] = field(default_factory=list)
    mood: str = ""
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class KnowledgeItem:
    title: str
    content: str
    source_url: str = ""
    source_type: str = "manual"
    category: str = ""
    tags: list[str] = field(default_factory=list)
    id: int | None = None
    created_at: datetime = field(default_factory=datetime.now)
