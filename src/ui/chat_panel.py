from __future__ import annotations

from PySide6.QtCore import Qt, Signal, Slot, QSize
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QScrollArea,
    QFrame,
    QLabel,
    QComboBox,
    QSizePolicy,
)

from .widgets.message_bubble import MessageBubble
from .widgets.streaming_text import StreamingTextWidget


class ChatPanel(QWidget):
    """AI chat interface with streaming responses."""

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._ai_engine = None
        self._messages: list[dict] = []
        self._setup_ui()

    def set_ai_engine(self, engine) -> None:
        self._ai_engine = engine
        engine.response_token.connect(self._on_token)
        engine.response_done.connect(self._on_response_done)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Model selector bar
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(12, 8, 12, 4)
        top_bar.addWidget(QLabel("模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "openai/gpt-4o",
            "anthropic/claude-sonnet-4-20250514",
            "ollama/llama3.1",
        ])
        self.model_combo.setEditable(True)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        top_bar.addWidget(self.model_combo)
        top_bar.addStretch()

        clear_btn = QPushButton("清空对话")
        clear_btn.clicked.connect(self._clear_chat)
        top_bar.addWidget(clear_btn)
        layout.addLayout(top_bar)

        # Message area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(12, 8, 12, 8)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()
        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

        # Streaming response area
        self.streaming_widget = StreamingTextWidget()
        self.streaming_widget.hide()
        layout.addWidget(self.streaming_widget)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setContentsMargins(12, 4, 12, 8)

        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.input_field.setPlaceholderText("输入消息... (Shift+Enter 换行，Enter 发送)")
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field)

        btn_layout = QVBoxLayout()
        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedWidth(80)
        self.send_btn.clicked.connect(self._send_message)
        btn_layout.addWidget(self.send_btn)
        btn_layout.addStretch()
        input_layout.addLayout(btn_layout)

        layout.addLayout(input_layout)

    def eventFilter(self, obj, event) -> bool:
        if obj == self.input_field and event.type() == event.Type.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    def _send_message(self) -> None:
        text = self.input_field.toPlainText().strip()
        if not text:
            return

        self.input_field.clear()
        self._add_message(text, is_user=True)
        self._messages.append({"role": "user", "content": text})

        if self._ai_engine:
            self.streaming_widget.clear()
            self.streaming_widget.show()
            self.send_btn.setEnabled(False)
            self._ai_engine.chat_stream(list(self._messages))

    def _add_message(self, text: str, is_user: bool) -> None:
        bubble = MessageBubble(text, is_user=is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        # Auto-scroll
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str)
    def _on_token(self, token: str) -> None:
        self.streaming_widget.append_text(token)
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    @Slot(str)
    def _on_response_done(self, full_text: str) -> None:
        self.streaming_widget.hide()
        self.send_btn.setEnabled(True)
        if full_text.strip():
            self._add_message(full_text, is_user=False)
            self._messages.append({"role": "assistant", "content": full_text})

    def _on_model_changed(self, model: str) -> None:
        if self._ai_engine:
            self._ai_engine.set_model(model)

    def _clear_chat(self) -> None:
        self._messages.clear()
        for i in range(self.messages_layout.count() - 1, -1, -1):
            widget = self.messages_layout.itemAt(i).widget()
            if widget and isinstance(widget, MessageBubble):
                widget.deleteLater()
