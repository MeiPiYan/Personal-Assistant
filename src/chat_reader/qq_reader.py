from __future__ import annotations

import json
import threading
import time
import urllib.request
import urllib.parse
from datetime import datetime

from PySide6.QtCore import Signal

from .base import ChatReaderBase
from ..storage.models import ChatMessage


class QQReader(ChatReaderBase):
    """QQ message reader via NapCat OneBot 11 HTTP API."""

    message_received = Signal(object)
    error = Signal(str)

    def __init__(self, base_url: str = "http://127.0.0.1:3000", parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip("/")
        self._polling = False
        self._polling_thread: threading.Thread | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────

    def start(self) -> bool:
        """Verify NapCat connection. Returns True on success."""
        super().start()
        try:
            info = self._get_login_info()
            nickname = info.get("nickname", "未知")
            user_id = info.get("user_id", "")
            print(f"[QQ] 已连接，当前账号: {nickname} ({user_id})")
            return True
        except Exception as e:
            self.error.emit(f"QQ 连接失败: {e}")
            self._running = False
            return False

    def stop(self) -> None:
        self._polling = False
        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=3)
        self._polling_thread = None
        super().stop()

    # ── Sync HTTP helpers (used from threads) ─────────────────────────

    def _http_get(self, endpoint: str, params: dict | None = None) -> dict:
        """Synchronous GET request to NapCat API."""
        url = f"{self.base_url}{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())

    def _get_login_info(self) -> dict:
        data = self._http_get("/get_login_info")
        return data.get("data", {})

    # ── Public query methods ──────────────────────────────────────────

    def get_group_list(self) -> list[dict]:
        """获取 QQ 群列表。"""
        try:
            data = self._http_get("/get_group_list")
            return data.get("data", [])
        except Exception as e:
            self.error.emit(f"获取 QQ 群列表失败: {e}")
            return []

    def get_friend_list(self) -> list[dict]:
        """获取 QQ 好友列表。"""
        try:
            data = self._http_get("/get_friend_list")
            return data.get("data", [])
        except Exception as e:
            self.error.emit(f"获取 QQ 好友列表失败: {e}")
            return []

    async def get_group_messages(self, group_id: int, count: int = 50) -> list[ChatMessage]:
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                resp = await session.get(
                    f"{self.base_url}/get_group_msg_history",
                    params={"group_id": group_id, "count": count},
                )
                data = await resp.json()
                messages = data.get("data", {}).get("messages", [])
                return [self._parse_msg(m) for m in messages]
        except Exception as e:
            self.error.emit(f"读取 QQ 群消息失败: {e}")
            return []

    async def get_friend_messages(self, user_id: int, count: int = 50) -> list[ChatMessage]:
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                resp = await session.get(
                    f"{self.base_url}/get_friend_msg_history",
                    params={"user_id": user_id, "count": count},
                )
                data = await resp.json()
                messages = data.get("data", {}).get("messages", [])
                return [self._parse_msg(m) for m in messages]
        except Exception as e:
            self.error.emit(f"读取 QQ 好友消息失败: {e}")
            return []

    # ── Polling ────────────────────────────────────────────────────────

    def start_polling(
        self,
        group_ids: list[int] | None = None,
        user_ids: list[int] | None = None,
        interval: float = 5.0,
    ) -> None:
        """Start thread-based polling for new QQ messages.

        Args:
            group_ids: QQ group IDs to monitor.
            user_ids: QQ friend user IDs to monitor.
            interval: Polling interval in seconds.
        """
        if self._polling:
            return
        if not group_ids and not user_ids:
            self.error.emit("未指定监听的 QQ 群或好友")
            return

        self._polling = True
        self._polling_thread = threading.Thread(
            target=self._poll_loop,
            args=(group_ids or [], user_ids or [], interval),
            daemon=True,
        )
        self._polling_thread.start()
        print(f"[QQ] 轮询已启动，监听 {len(group_ids or [])} 个群, {len(user_ids or [])} 个好友, 间隔 {interval}s")

    def _poll_loop(
        self,
        group_ids: list[int],
        user_ids: list[int],
        interval: float,
    ) -> None:
        """Background polling loop — runs in a daemon thread."""
        last_msg_ids: dict[str, int] = {}

        while self._polling:
            # ── Poll groups ──
            for gid in group_ids:
                try:
                    data = self._http_get(
                        "/get_group_msg_history",
                        {"group_id": gid, "count": 10},
                    )
                    messages = data.get("data", {}).get("messages", [])
                    key = f"group_{gid}"
                    last_id = last_msg_ids.get(key, 0)

                    new_msgs = [
                        m for m in messages
                        if m.get("message_id", 0) > last_id
                    ]
                    # Emit oldest-first
                    for m in reversed(new_msgs):
                        msg = self._parse_msg(m)
                        self.message_received.emit(msg)

                    if messages:
                        last_msg_ids[key] = max(
                            m.get("message_id", 0) for m in messages
                        )
                except Exception as e:
                    self.error.emit(f"QQ 群 {gid} 轮询出错: {e}")

            # ── Poll friends ──
            for uid in user_ids:
                try:
                    data = self._http_get(
                        "/get_friend_msg_history",
                        {"user_id": uid, "count": 10},
                    )
                    messages = data.get("data", {}).get("messages", [])
                    key = f"friend_{uid}"
                    last_id = last_msg_ids.get(key, 0)

                    new_msgs = [
                        m for m in messages
                        if m.get("message_id", 0) > last_id
                    ]
                    for m in reversed(new_msgs):
                        msg = self._parse_msg(m)
                        self.message_received.emit(msg)

                    if messages:
                        last_msg_ids[key] = max(
                            m.get("message_id", 0) for m in messages
                        )
                except Exception as e:
                    self.error.emit(f"QQ 好友 {uid} 轮询出错: {e}")

            time.sleep(interval)

    # ── Message parsing ────────────────────────────────────────────────

    def _parse_msg(self, raw: dict) -> ChatMessage:
        message = raw.get("message", "")
        if isinstance(message, list):
            # OneBot CQ code / segment format
            parts = []
            for seg in message:
                if seg.get("type") == "text":
                    parts.append(seg.get("data", {}).get("text", ""))
                elif seg.get("type") == "image":
                    parts.append("[图片]")
                elif seg.get("type") == "face":
                    parts.append("[表情]")
                elif seg.get("type") == "record":
                    parts.append("[语音]")
                elif seg.get("type") == "video":
                    parts.append("[视频]")
                elif seg.get("type") == "at":
                    parts.append(f"@{seg.get('data', {}).get('qq', '')}")
            message = "".join(parts)

        # Timestamp
        msg_time = raw.get("time", 0)
        if isinstance(msg_time, (int, float)) and msg_time > 0:
            try:
                created_at = datetime.fromtimestamp(msg_time)
            except Exception:
                created_at = datetime.now()
        else:
            created_at = datetime.now()

        # Sender — prefer card (group card name), then nickname
        sender_obj = raw.get("sender", {})
        sender_name = (
            sender_obj.get("card")
            or sender_obj.get("nickname")
            or str(sender_obj.get("user_id", ""))
        )

        # Group info — use group_id as group_name for QQ
        group_id = raw.get("group_id", "")
        group_name = str(group_id) if group_id else ""

        return ChatMessage(
            platform="qq",
            sender=sender_name,
            content=message,
            group_name=group_name,
            msg_type="text",
            raw_data=str(raw),
            created_at=created_at,
        )
