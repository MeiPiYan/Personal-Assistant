from __future__ import annotations

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QScrollArea, QCheckBox, QComboBox,
    QLineEdit, QListWidget, QListWidgetItem, QSplitter,
)
from PySide6.QtGui import QFont

from .widgets.message_bubble import MessageBubble
from ..chat_reader.wechat_reader import WeChatReader
from ..chat_reader.models import ChatMessage


class ChatReaderPanel(QWidget):
    """Live chat message stream from WeChat/QQ."""

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._wechat_reader: WeChatReader | None = None
        self._qq_reader = None
        self._selected_sessions: list[str] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("消息监控")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 0;")
        layout.addWidget(header)

        # Platform controls
        ctrl_layout = QHBoxLayout()
        self.wechat_cb = QCheckBox("微信")
        self.wechat_cb.stateChanged.connect(self._on_wechat_toggled)
        ctrl_layout.addWidget(self.wechat_cb)

        self.qq_cb = QCheckBox("QQ")
        ctrl_layout.addWidget(self.qq_cb)

        ctrl_layout.addStretch()

        self.refresh_btn = QPushButton("刷新会话")
        self.refresh_btn.clicked.connect(self._on_refresh_sessions)
        ctrl_layout.addWidget(self.refresh_btn)

        self.start_btn = QPushButton("开始监控")
        self.start_btn.clicked.connect(self._on_toggle_monitoring)
        self.start_btn.setEnabled(False)
        ctrl_layout.addWidget(self.start_btn)
        layout.addLayout(ctrl_layout)

        # Session selector
        session_layout = QHBoxLayout()
        session_layout.addWidget(QLabel("选择会话:"))
        self.session_combo = QComboBox()
        self.session_combo.setMinimumWidth(200)
        self.session_combo.currentIndexChanged.connect(self._on_session_selected)
        session_layout.addWidget(self.session_combo)
        session_layout.addStretch()
        layout.addLayout(session_layout)

        # Main content: messages + summary
        splitter = QSplitter(Qt.Vertical)

        # Message stream
        msg_widget = QWidget()
        msg_layout = QVBoxLayout(msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        msg_layout.addWidget(QLabel("实时消息:"))
        self.message_area = QScrollArea()
        self.message_area.setWidgetResizable(True)
        self.message_container = QWidget()
        self.message_layout = QVBoxLayout(self.message_container)
        self.message_layout.setSpacing(4)
        self.message_layout.setAlignment(Qt.AlignTop)
        self.message_area.setWidget(self.message_container)
        msg_layout.addWidget(self.message_area)
        splitter.addWidget(msg_widget)

        # AI Summary area
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)
        summary_layout.addWidget(QLabel("AI 摘要:"))
        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        summary_layout.addWidget(self.summary_output)
        splitter.addWidget(summary_widget)

        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

        # Status bar
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #6c7086; font-size: 12px;")
        layout.addWidget(self.status_label)

        self._monitoring = False

    def _on_wechat_toggled(self, state: int) -> None:
        if state == Qt.Checked:
            self._init_wechat()
        else:
            self._stop_wechat()

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
            self.start_btn.setEnabled(False)
            self.session_combo.clear()

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
            self.status_label.setText(f"正在加载 [{self.session_combo.currentText()}] 的消息...")
            messages = self._wechat_reader.get_messages(username, limit=20)
            self._display_messages(messages)
            self.status_label.setText(f"已加载 {len(messages)} 条消息")

    def _display_messages(self, messages: list[ChatMessage]) -> None:
        # Clear existing messages
        while self.message_layout.count():
            item = self.message_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        for msg in reversed(messages):  # Oldest first
            is_self = msg.sender == "我"
            time_str = msg.created_at.strftime("%H:%M") if msg.created_at else ""
            display = f"[{time_str}] {msg.sender}: {msg.content[:100]}"
            bubble = MessageBubble(display, is_user=is_self)
            self.message_layout.addWidget(bubble)

    def _on_toggle_monitoring(self) -> None:
        self._monitoring = not self._monitoring
        if self._monitoring:
            self.start_btn.setText("停止监控")
            sessions = []
            if self.wechat_cb.isChecked() and self._wechat_reader:
                current = self.session_combo.currentData()
                if current:
                    sessions.append(current)
                self._wechat_reader.start_polling(sessions, interval=5.0)
            self.status_label.setText("监控中...")
        else:
            self.start_btn.setText("开始监控")
            if self._wechat_reader:
                self._wechat_reader._polling = False
            self.status_label.setText("已停止监控")

    @Slot(object)
    def _on_message(self, msg: ChatMessage) -> None:
        is_self = msg.sender == "我"
        time_str = msg.created_at.strftime("%H:%M") if msg.created_at else ""
        display = f"[{time_str}] {msg.sender}: {msg.content[:100]}"
        bubble = MessageBubble(display, is_user=is_self)
        self.message_layout.addWidget(bubble)
        # Auto-scroll
        sb = self.message_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str)
    def _on_error(self, error: str) -> None:
        self.status_label.setText(f"错误: {error}")
