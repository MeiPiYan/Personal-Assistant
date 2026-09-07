from __future__ import annotations

import threading
from datetime import datetime

from PySide6.QtCore import Signal

from .base import ChatReaderBase
from ..storage.models import ChatMessage


class WeChatReader(ChatReaderBase):
    """WeChat message reader using wechatauto-replica DB decryption.

    API: from wechatauto import WeChatDB
    db = WeChatDB()
    db.get_sessions(limit=10)
    db.get_messages(username, limit=50)
    """

    message_received = Signal(object)
    session_list_updated = Signal(list)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db = None
        self._listener = None
        self._listener_thread = None
        self._polling = False

    def start(self) -> None:
        super().start()
        try:
            from wechatauto import WeChatDB
            self._db = WeChatDB()
            # Verify connection by getting self info
            info = self._db.get_self_info()
            nickname = info.get("nickname", "未知") if info else "未知"
            print(f"[WeChat] 已连接，当前账号: {nickname}")
        except ImportError:
            self.error.emit("wechatauto-replica 未安装。请运行: pip install wechatauto-replica")
        except Exception as e:
            self.error.emit(f"WeChat 初始化失败: {e}")

    def get_sessions(self, limit: int = 20) -> list[dict]:
        """获取会话列表（最近聊天）。"""
        if not self._db:
            return []
        try:
            sessions = self._db.get_sessions(limit=limit)
            result = []
            for s in sessions:
                username = s.get("username", "")
                nickname = self._db.get_nickname(username) or username
                result.append({
                    "username": username,
                    "nickname": nickname,
                    "unread": s.get("unread", 0),
                    "digest": s.get("digest", ""),
                    "time": s.get("time", ""),
                })
            self.session_list_updated.emit(result)
            return result
        except Exception as e:
            self.error.emit(f"获取会话列表失败: {e}")
            return []

    def get_messages(self, username: str, limit: int = 50) -> list[ChatMessage]:
        """获取指定会话的消息。"""
        if not self._db:
            return []
        try:
            raw_msgs = self._db.get_messages(username, limit=limit)
            messages = []
            for m in raw_msgs:
                msg = self._parse_message(m, username)
                if msg:
                    messages.append(msg)
            return messages
        except Exception as e:
            self.error.emit(f"读取微信消息失败: {e}")
            return []

    def search_contact(self, keyword: str) -> list[dict]:
        """搜索联系人。"""
        if not self._db:
            return []
        try:
            return self._db.search_contact(keyword)
        except Exception as e:
            self.error.emit(f"搜索联系人失败: {e}")
            return []

    def start_polling(self, chat_usernames: list[str], interval: float = 5.0) -> None:
        """启动轮询监听新消息。

        Args:
            chat_usernames: 要监听的会话 username 列表
            interval: 轮询间隔（秒）
        """
        if not self._db:
            self.error.emit("WeChat 未初始化")
            return

        self._polling = True

        def poll_loop():
            last_ids = {}
            while self._polling:
                try:
                    for username in chat_usernames:
                        msgs = self._db.get_messages(username, limit=10)
                        last_id = last_ids.get(username, 0)
                        new_msgs = [m for m in msgs if m.get("server_id", 0) > last_id]
                        for m in new_msgs:
                            msg = self._parse_message(m, username)
                            if msg:
                                self.message_received.emit(msg)
                        if msgs:
                            last_ids[username] = max(
                                m.get("server_id", 0) for m in msgs
                            )
                except Exception as e:
                    self.error.emit(f"轮询出错: {e}")

                import time
                time.sleep(interval)

        self._listener_thread = threading.Thread(target=poll_loop, daemon=True)
        self._listener_thread.start()

    def start_listener(self, chat_usernames: list[str]) -> None:
        """使用 wechatauto 内置 Listener 监听消息（推荐方式）。

        Args:
            chat_usernames: 要监听的会话 username 列表
        """
        if not self._db:
            self.error.emit("WeChat 未初始化")
            return

        try:
            from wechatauto import Listener

            self._listener = Listener(self._db)

            for username in chat_usernames:
                self._listener.add(username)

            def on_message(msg):
                chat_username = msg.get("chat_username", "")
                parsed = self._parse_message(msg, chat_username)
                if parsed:
                    self.message_received.emit(parsed)

            self._listener.start(callback=on_message)
            print(f"[WeChat] Listener 已启动，监听 {len(chat_usernames)} 个会话")
        except Exception as e:
            self.error.emit(f"启动 Listener 失败: {e}")

    def stop_listener(self) -> None:
        """停止 Listener。"""
        if self._listener:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def _parse_message(self, raw: dict, chat_username: str = "") -> ChatMessage | None:
        """将 wechatauto 消息字典解析为 ChatMessage。"""
        content = raw.get("content", "")
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8", errors="ignore")
            except Exception:
                content = str(content)

        msg_type = raw.get("type", "text")
        # Map wechatauto type to our type
        type_map = {
            1: "text",       # 文本
            3: "image",      # 图片
            34: "voice",     # 语音
            43: "video",     # 视频
            47: "emotion",   # 表情
            49: "link",      # 链接/文件
            10000: "system", # 系统消息
            10002: "system", # 撤回消息
        }
        if isinstance(msg_type, int):
            msg_type = type_map.get(msg_type, "text")
        elif isinstance(msg_type, str) and msg_type not in ("text", "image", "voice", "video", "emotion", "link", "system", "file"):
            msg_type = "text"

        sender_id = raw.get("sender_id", "")
        # In group chats, sender_id is the actual sender
        # In private chats, sender_id indicates self (2) or friend
        if str(sender_id) == "2":
            sender_display = "我"
        else:
            sender_display = raw.get("sender_name", str(sender_id))

        create_time = raw.get("create_time", 0)
        if isinstance(create_time, (int, float)) and create_time > 0:
            try:
                dt = datetime.fromtimestamp(create_time)
            except Exception:
                dt = datetime.now()
        else:
            dt = datetime.now()

        return ChatMessage(
            platform="wechat",
            sender=sender_display,
            content=content,
            group_name=chat_username if raw.get("is_group") else "",
            msg_type=msg_type,
            raw_data=str(raw),
            created_at=dt,
        )

    def stop(self) -> None:
        self._polling = False
        self.stop_listener()
        self._db = None
        super().stop()
