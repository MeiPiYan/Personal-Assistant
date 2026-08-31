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
