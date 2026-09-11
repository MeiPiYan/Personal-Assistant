"""AI Chat panel with streaming responses."""

from __future__ import annotations

import asyncio

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QScrollArea, QLabel, QComboBox,
    QSizePolicy, QFrame,
)
from PySide6.QtGui import QFont

from .styles import ThemeManager
from .widgets.message_bubble import MessageBubble
from .widgets.streaming_text import StreamingTextWidget
from ..ai.models import (
    CLOUD_PROVIDERS, PROVIDER_NAMES, PROVIDER_MODELS,
    get_all_model_strings, get_default_model,
)
from ..ai.prompts import build_chat_messages
from ..storage.dao import DAO


class ChatPanel(QWidget):
    """AI chat interface with streaming responses."""

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._ai_engine = None
        self._dao: DAO | None = None
        self._messages: list[dict] = []
        self._setup_ui()
        ThemeManager.register_panel(self)

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self._model_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._divider.setStyleSheet(
            f"background-color: {c.divider}; max-height: 1px;"
        )
        self._welcome_label.setStyleSheet(
            f"color: {c.text_disabled}; font-size: 15px; padding: 60px 0;"
        )

    def set_ai_engine(self, engine) -> None:
        self._ai_engine = engine
        engine.response_token.connect(self._on_token)
        engine.response_done.connect(self._on_response_done)
        engine.error.connect(self._on_error)

    def set_dao(self, dao: DAO) -> None:
        """Accept DAO instance and load persisted chat history."""
        self._dao = dao
        asyncio.ensure_future(self._load_history())

    def _setup_ui(self) -> None:
        c = ThemeManager.get_colors()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Top bar: model selector ---
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(16, 10, 16, 8)

        self._model_label = QLabel("模型")
        self._model_label.setStyleSheet(f"color: {c.text_secondary}; font-size: 12px;")
        top_bar.addWidget(self._model_label)

        self.model_combo = QComboBox()
        self.model_combo.setFixedWidth(300)
        self.model_combo.setEditable(True)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        top_bar.addWidget(self.model_combo)

        top_bar.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("secondaryBtn")
        clear_btn.setFixedWidth(64)
        clear_btn.clicked.connect(self._clear_chat)
        top_bar.addWidget(clear_btn)

        layout.addLayout(top_bar)

        # Divider
        self._divider = QFrame()
        self._divider.setFrameShape(QFrame.HLine)
        self._divider.setStyleSheet(f"background-color: {c.divider}; max-height: 1px;")
        layout.addWidget(self._divider)

        # --- Messages area ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(20, 16, 20, 16)
        self.messages_layout.setSpacing(10)
        self.messages_layout.addStretch()

        # Welcome message
        welcome = QLabel("你好！有什么我可以帮忙的？")
        welcome.setAlignment(Qt.AlignCenter)
        welcome.setStyleSheet(f"color: {c.text_disabled}; font-size: 15px; padding: 60px 0;")
        self._welcome_label = welcome
        self.messages_layout.insertWidget(0, welcome)

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area, 1)

        # --- Streaming widget ---
        self.streaming_widget = StreamingTextWidget()
        self.streaming_widget.hide()
        layout.addWidget(self.streaming_widget)

        # --- Input area ---
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(16, 8, 16, 14)
        input_layout.setSpacing(10)

        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText("输入消息... (Enter 发送, Shift+Enter 换行)")
        self.input_field.setMaximumHeight(100)
        self.input_field.setMinimumHeight(44)
        self.input_field.installEventFilter(self)
        input_layout.addWidget(self.input_field, 1)

        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedWidth(72)
        self.send_btn.setMinimumHeight(44)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(input_container)

    def load_models_from_config(self) -> None:
        """Load models based on current config settings."""
        self.model_combo.blockSignals(True)
        self.model_combo.clear()

        if not self.app or not self.app.config:
            self.model_combo.addItems(get_all_model_strings())
            self.model_combo.blockSignals(False)
            return

        cfg = self.app.config
        provider = cfg.get("ai.default_provider", "deepseek")
        model_id = cfg.get("ai.default_model", "deepseek-chat")

        # Get models for current provider
        models = PROVIDER_MODELS.get(provider, [])
        provider_name = PROVIDER_NAMES.get(provider, provider)

        for model_name, display_name, _ in models:
            full_name = f"{provider}/{model_name}"
            self.model_combo.addItem(f"{display_name} ({provider_name})", full_name)

        # Set current model
        current_full = f"{provider}/{model_id}"
        idx = self.model_combo.findData(current_full)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setEditText(current_full)

        self.model_combo.blockSignals(False)

        # Update AI engine
        if self._ai_engine:
            self._ai_engine.set_model(current_full)

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

        # Persist user message to database
        if self._dao:
            model = self.model_combo.currentData() or ""
            asyncio.ensure_future(
                self._dao.insert_chat_history("user", text, model=model)
            )

        if self._ai_engine:
            self._hide_welcome()
            self.streaming_widget.clear()
            self.streaming_widget.show()
            self.send_btn.setEnabled(False)

            # Get selected model
            model = self.model_combo.currentData()
            if model:
                self._ai_engine.set_model(model)

            # Build messages with system prompt
            # Extract chat history (excluding the latest user message), capped
            # so the payload doesn't grow without bound over long sessions.
            chat_history = self._messages[:-1] if len(self._messages) > 1 else []
            chat_history = chat_history[-20:]
            api_messages = build_chat_messages(text, chat_history)

            # Run async chat_stream via asyncio task
            asyncio.ensure_future(self._ai_engine.chat_stream(api_messages))

    def _add_message(self, text: str, is_user: bool) -> None:
        bubble = MessageBubble(text, is_user=is_user)
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _hide_welcome(self) -> None:
        if self._welcome_label and self._welcome_label.isVisible():
            self._welcome_label.hide()

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

            # Persist assistant response to database
            if self._dao:
                model = self.model_combo.currentData() or ""
                asyncio.ensure_future(
                    self._dao.insert_chat_history("assistant", full_text, model=model)
                )

    @Slot(str)
    def _on_error(self, error: str) -> None:
        self.streaming_widget.hide()
        self.send_btn.setEnabled(True)
        self._add_message(f"[错误] {error}", is_user=False)

    def _on_model_changed(self, index: int) -> None:
        model = self.model_combo.currentData()
        if model and self._ai_engine:
            self._ai_engine.set_model(model)

    def _clear_chat(self) -> None:
        self._messages.clear()
        for i in range(self.messages_layout.count() - 1, -1, -1):
            widget = self.messages_layout.itemAt(i).widget()
            if widget and isinstance(widget, MessageBubble):
                widget.deleteLater()
        if self._welcome_label:
            self._welcome_label.show()
        # Also clear persisted history
        if self._dao:
            asyncio.ensure_future(self._dao.clear_chat_history())

    async def _load_history(self, limit: int = 50) -> None:
        """Load recent chat history from database and display it."""
        if self._dao is None:
            return
        try:
            rows = await self._dao.get_chat_history(limit=limit)
            if not rows:
                return

            # Hide welcome label when we have history
            self._hide_welcome()

            # Rebuild in-memory message list and display bubbles
            for row in rows:
                role = row.get("role", "")
                content = row.get("content", "")
                if not content:
                    continue
                is_user = role == "user"
                self._messages.append({"role": role, "content": content})
                self._add_message(content, is_user=is_user)
        except Exception as e:
            print(f"[ChatPanel] Failed to load chat history: {e}")
