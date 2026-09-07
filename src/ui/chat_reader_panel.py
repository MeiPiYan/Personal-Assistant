"""Chat reader panel - live message monitoring from WeChat/QQ."""

from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QScrollArea, QCheckBox, QComboBox,
    QSplitter, QFrame, QLineEdit,
)

from .styles import ThemeManager
from .widgets.message_bubble import MessageBubble
from ..chat_reader.wechat_reader import WeChatReader
from ..chat_reader.qq_reader import QQReader
from ..storage.models import ChatMessage
from ..app.config import Config


class ChatReaderPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._wechat_reader: WeChatReader | None = None
        self._qq_reader: QQReader | None = None
        self._selected_sessions: list[str] = []
        self._monitoring = False
        self._setup_ui()
        ThemeManager.register_panel(self)

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self._qq_group_label.setStyleSheet(
            f"color: {c.text_tertiary}; font-size: 12px;"
        )
        self._qq_friend_label.setStyleSheet(
            f"color: {c.text_tertiary}; font-size: 12px;"
        )
        self._msg_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._summary_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._status_label.setStyleSheet(
            f"color: {c.text_disabled}; font-size: 12px;"
        )

    def _setup_ui(self) -> None:
        c = ThemeManager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("消息监控")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # ── Controls row 1: platform checkboxes + session + buttons ───
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self.wechat_cb = QCheckBox("微信")
        self.wechat_cb.stateChanged.connect(self._on_wechat_toggled)
        ctrl_row.addWidget(self.wechat_cb)

        self.qq_cb = QCheckBox("QQ")
        self.qq_cb.stateChanged.connect(self._on_qq_toggled)
        ctrl_row.addWidget(self.qq_cb)

        ctrl_row.addStretch()

        self.session_combo = QComboBox()
        self.session_combo.setMinimumWidth(180)
        self.session_combo.currentIndexChanged.connect(self._on_session_selected)
        ctrl_row.addWidget(self.session_combo)

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setObjectName("secondaryBtn")
        self.refresh_btn.setFixedWidth(56)
        self.refresh_btn.clicked.connect(self._on_refresh_sessions)
        ctrl_row.addWidget(self.refresh_btn)

        self.start_btn = QPushButton("开始监控")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self._on_toggle_monitoring)
        ctrl_row.addWidget(self.start_btn)

        layout.addLayout(ctrl_row)

        # ── Controls row 2: QQ group ID input (hidden by default) ─────
        self._qq_row = QWidget()
        qq_row_layout = QHBoxLayout(self._qq_row)
        qq_row_layout.setContentsMargins(0, 0, 0, 0)
        qq_row_layout.setSpacing(8)

        self._qq_group_label = QLabel("QQ 群号:")
        self._qq_group_label.setStyleSheet(
            f"color: {c.text_tertiary}; font-size: 12px;"
        )
        qq_row_layout.addWidget(self._qq_group_label)

        self.qq_groups_input = QLineEdit()
        self.qq_groups_input.setPlaceholderText("多个群号用逗号分隔，如 123456,789012")
        self.qq_groups_input.setMinimumWidth(200)
        qq_row_layout.addWidget(self.qq_groups_input, 1)

        self._qq_friend_label = QLabel("好友QQ号:")
        self._qq_friend_label.setStyleSheet(
            f"color: {c.text_tertiary}; font-size: 12px;"
        )
        qq_row_layout.addWidget(self._qq_friend_label)

        self.qq_friends_input = QLineEdit()
        self.qq_friends_input.setPlaceholderText("多个QQ号用逗号分隔")
        self.qq_friends_input.setMinimumWidth(160)
        qq_row_layout.addWidget(self.qq_friends_input, 1)

        self._qq_row.setVisible(False)
        layout.addWidget(self._qq_row)

        # ── Messages + Summary splitter ────────────────────────────────
        splitter = QSplitter(Qt.Vertical)

        # Messages
        msg_widget = QWidget()
        msg_layout = QVBoxLayout(msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.setSpacing(4)

        self._msg_label = QLabel("实时消息")
        self._msg_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        msg_layout.addWidget(self._msg_label)

        self.message_area = QScrollArea()
        self.message_area.setWidgetResizable(True)
        self.message_area.setFrameShape(QFrame.NoFrame)
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setSpacing(4)
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_area.setWidget(self.message_container)
        msg_layout.addWidget(self.message_area)
        splitter.addWidget(msg_widget)

        # Summary
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.setSpacing(4)

        self._summary_label = QLabel("AI 摘要")
        self._summary_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        summary_layout.addWidget(self._summary_label)

        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("AI 摘要将在此显示...")
        summary_layout.addWidget(self.summary_output)
        splitter.addWidget(summary_widget)

        splitter.setSizes([350, 150])
        layout.addWidget(splitter, 1)

        # Status
        self._status_label = QLabel("就绪")
        self._status_label.setStyleSheet(
            f"color: {c.text_disabled}; font-size: 12px;"
        )
        layout.addWidget(self._status_label)
        # Keep public reference
        self.status_label = self._status_label

    # ── Platform toggles ──────────────────────────────────────────────

    def _on_wechat_toggled(self, state: int) -> None:
        if state == Qt.Checked:
            self._init_wechat()
        else:
            self._stop_wechat()
        self._update_start_btn()

    def _on_qq_toggled(self, state: int) -> None:
        if state == Qt.Checked:
            self._init_qq()
        else:
            self._stop_qq()
        self._update_start_btn()

    def _update_start_btn(self) -> None:
        """Enable the start button when at least one platform is connected."""
        wechat_ok = self._wechat_reader is not None and self._wechat_reader._db is not None
        qq_ok = self._qq_reader is not None and self._qq_reader.is_running
        self.start_btn.setEnabled(wechat_ok or qq_ok)

    # ── WeChat ────────────────────────────────────────────────────────

    def _init_wechat(self) -> None:
        if self._wechat_reader:
            return
        self.status_label.setText("正在连接微信...")
        self._wechat_reader = WeChatReader()
        self._wechat_reader.error.connect(self._on_error)
        self._wechat_reader.message_received.connect(self._on_message)
        self._wechat_reader.start()

        if self._wechat_reader._db:
            self.status_label.setText("微信已连接")
            self.start_btn.setEnabled(True)
            self._on_refresh_sessions()
        else:
            self.status_label.setText("微信连接失败")

    def _stop_wechat(self) -> None:
        if self._wechat_reader:
            self._wechat_reader.stop()
            self._wechat_reader = None
            self.session_combo.clear()

    # ── QQ ────────────────────────────────────────────────────────────

    def _init_qq(self) -> None:
        if self._qq_reader:
            return
        self.status_label.setText("正在连接 QQ (NapCat)...")
        cfg = Config()
        napcat_url = cfg.get("chat_reader.qq.napcat_url", "http://127.0.0.1:3000")

        self._qq_reader = QQReader(base_url=napcat_url)
        self._qq_reader.error.connect(self._on_error)
        self._qq_reader.message_received.connect(self._on_message)

        success = self._qq_reader.start()
        if success:
            self.status_label.setText("QQ 已连接")
            self._qq_row.setVisible(True)
            self.start_btn.setEnabled(True)
            # Try to auto-populate group list
            self._qq_populate_group_list()
        else:
            self._qq_reader = None
            self.status_label.setText("QQ 连接失败，请检查 NapCat 是否运行")

    def _stop_qq(self) -> None:
        if self._qq_reader:
            self._qq_reader.stop()
            self._qq_reader = None
            self._qq_row.setVisible(False)

    def _qq_populate_group_list(self) -> None:
        """Fetch QQ group list and show count in status."""
        if not self._qq_reader:
            return
        try:
            groups = self._qq_reader.get_group_list()
            friends = self._qq_reader.get_friend_list()
            parts = []
            if groups:
                parts.append(f"{len(groups)} 个群")
            if friends:
                parts.append(f"{len(friends)} 个好友")
            detail = ", ".join(parts) if parts else "暂无群/好友"
            self.status_label.setText(f"QQ 已连接 — {detail}")
        except Exception:
            pass  # non-critical

    # ── Sessions ──────────────────────────────────────────────────────

    def _on_refresh_sessions(self) -> None:
        if not self._wechat_reader:
            return
        self.status_label.setText("正在获取会话列表...")
        sessions = self._wechat_reader.get_sessions(limit=30)
        self.session_combo.clear()
        self._session_map = {}
        for s in sessions:
            username = s["username"]
            nickname = s["nickname"]
            unread = s["unread"]
            display = f"{nickname}" + (f" ({unread}条未读)" if unread > 0 else "")
            self.session_combo.addItem(display, userData=username)
            self._session_map[display] = s
        self.status_label.setText(f"已加载 {len(sessions)} 个会话")

    def _on_session_selected(self, index: int) -> None:
        if index < 0:
            return
        username = self.session_combo.currentData()
        if username and self._wechat_reader:
            self.status_label.setText("正在加载消息...")
            messages = self._wechat_reader.get_messages(username, limit=20)
            self._display_messages(messages)
            self.status_label.setText(f"已加载 {len(messages)} 条消息")

    # ── Display ────────────────────────────────────────────────────────

    def _display_messages(self, messages: list[ChatMessage]) -> None:
        while self.message_layout.count():
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for msg in reversed(messages):
            bubble = self._make_bubble(msg)
            self.message_layout.addWidget(bubble)

    def _make_bubble(self, msg: ChatMessage) -> MessageBubble:
        """Create a MessageBubble for a ChatMessage with platform-aware formatting."""
        is_self = msg.sender == "我"
        time_str = msg.created_at.strftime("%H:%M") if msg.created_at else ""

        # Platform prefix for QQ messages
        platform_prefix = ""
        if msg.platform == "qq":
            if msg.group_name:
                platform_prefix = f"[群{msg.group_name}] "
            else:
                platform_prefix = "[QQ] "

        display = f"[{time_str}] {platform_prefix}{msg.sender}: {msg.content[:100]}"
        return MessageBubble(display, is_user=is_self)

    # ── Monitoring ────────────────────────────────────────────────────

    def _on_toggle_monitoring(self) -> None:
        self._monitoring = not self._monitoring
        if self._monitoring:
            self.start_btn.setText("停止监控")

            # Start WeChat polling
            if self.wechat_cb.isChecked() and self._wechat_reader:
                sessions = []
                current = self.session_combo.currentData()
                if current:
                    sessions.append(current)
                if sessions:
                    self._wechat_reader.start_polling(sessions, interval=5.0)

            # Start QQ polling
            if self.qq_cb.isChecked() and self._qq_reader:
                group_ids = self._parse_qq_ids(self.qq_groups_input.text())
                user_ids = self._parse_qq_ids(self.qq_friends_input.text())
                if group_ids or user_ids:
                    cfg = Config()
                    interval = cfg.get("chat_reader.qq.poll_interval", 5)
                    self._qq_reader.start_polling(
                        group_ids=group_ids,
                        user_ids=user_ids,
                        interval=float(interval),
                    )
                else:
                    self.status_label.setText("QQ 监控: 请输入群号或好友QQ号")

            self.status_label.setText("监控中...")
        else:
            self.start_btn.setText("开始监控")
            if self._wechat_reader:
                self._wechat_reader._polling = False
            if self._qq_reader:
                self._qq_reader._polling = False
            self.status_label.setText("已停止监控")

    @staticmethod
    def _parse_qq_ids(text: str) -> list[int]:
        """Parse comma/space-separated QQ IDs into a list of ints."""
        ids = []
        for part in text.replace("，", ",").split(","):
            part = part.strip()
            if part.isdigit():
                ids.append(int(part))
        return ids

    # ── Slots ─────────────────────────────────────────────────────────

    @Slot(object)
    def _on_message(self, msg: ChatMessage) -> None:
        bubble = self._make_bubble(msg)
        self.message_layout.addWidget(bubble)
        sb = self.message_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str)
    def _on_error(self, error: str) -> None:
        self.status_label.setText(f"错误: {error}")
