from __future__ import annotations

import aiohttp
from .base import ChatReaderBase
from .models import ChatMessage


class QQReader(ChatReaderBase):
    """QQ message reader via NapCat OneBot 11 HTTP API."""

    def __init__(self, base_url: str = "http://127.0.0.1:3000", parent=None):
        super().__init__(parent)
        self.base_url = base_url

    async def get_group_messages(self, group_id: int, count: int = 50) -> list[ChatMessage]:
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    f"{self.base_url}/get_group_msg_history",
                    params={"group_id": group_id, "count": count},
                )
                data = await resp.json()
                messages = data.get("data", {}).get("messages", [])
                return [self._parse_msg(m) for m in messages]
        except Exception as e:
            self.error.emit(f"读取 QQ 消息失败: {e}")
            return []

    async def get_friend_messages(self, user_id: int, count: int = 50) -> list[ChatMessage]:
        try:
            async with aiohttp.ClientSession() as session:
                resp = await session.get(
                    f"{self.base_url}/get_friend_msg_history",
                    params={"user_id": user_id, "count": count},
                )
                data = await resp.json()
                messages = data.get("data", {}).get("messages", [])
                return [self._parse_msg(m) for m in messages]
        except Exception as e:
            self.error.emit(f"读取 QQ 消息失败: {e}")
            return []

    def _parse_msg(self, raw: dict) -> ChatMessage:
        message = raw.get("message", "")
        if isinstance(message, list):
            # OneBot CQ code format
            parts = []
            for seg in message:
                if seg.get("type") == "text":
                    parts.append(seg.get("data", {}).get("text", ""))
            message = "".join(parts)

        return ChatMessage(
            platform="qq",
            sender=str(raw.get("sender", {}).get("user_id", "")),
            content=message,
            group_name=str(raw.get("sender", {}).get("nickname", "")),
            msg_type="text",
            raw_data=str(raw),
        )
