"""Settings panel for API keys and configuration."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QFormLayout,
    QCheckBox, QScrollArea, QFrame,
)


class SettingsPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self) -> None:
        # Scrollable wrapper
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        header = QLabel("设置")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # AI Provider
        ai_group = QGroupBox("AI 模型配置")
        ai_form = QFormLayout()

        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.Password)
        self.openai_key.setPlaceholderText("sk-...")
        ai_form.addRow("OpenAI Key:", self.openai_key)

        self.anthropic_key = QLineEdit()
        self.anthropic_key.setEchoMode(QLineEdit.Password)
        self.anthropic_key.setPlaceholderText("sk-ant-...")
        ai_form.addRow("Anthropic Key:", self.anthropic_key)

        self.ollama_url = QLineEdit()
        self.ollama_url.setText("http://localhost:11434")
        ai_form.addRow("Ollama 地址:", self.ollama_url)

        self.custom_url = QLineEdit()
        self.custom_url.setPlaceholderText("http://localhost:8000/v1")
        ai_form.addRow("自定义 API:", self.custom_url)

        self.custom_key = QLineEdit()
        self.custom_key.setEchoMode(QLineEdit.Password)
        ai_form.addRow("自定义 Key:", self.custom_key)

        ai_group.setLayout(ai_form)
        layout.addWidget(ai_group)

        # Chat Reader
        reader_group = QGroupBox("消息读取")
        reader_form = QFormLayout()

        self.wechat_enabled = QCheckBox("启用微信消息读取")
        reader_form.addRow(self.wechat_enabled)

        self.qq_enabled = QCheckBox("启用 QQ 消息读取")
        reader_form.addRow(self.qq_enabled)

        self.napcat_url = QLineEdit()
        self.napcat_url.setText("http://127.0.0.1:3000")
        reader_form.addRow("NapCat 地址:", self.napcat_url)

        reader_group.setLayout(reader_form)
        layout.addWidget(reader_group)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)
        layout.addLayout(btn_row)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

        self._load_settings()

    def _load_settings(self) -> None:
        if not self.app or not self.app.config:
            return
        cfg = self.app.config
        self.openai_key.setText(cfg.get("ai.providers.openai.api_key", ""))
        self.anthropic_key.setText(cfg.get("ai.providers.anthropic.api_key", ""))
        self.ollama_url.setText(cfg.get("ai.providers.ollama.base_url", "http://localhost:11434"))
        self.custom_url.setText(cfg.get("ai.providers.custom.base_url", ""))
        self.custom_key.setText(cfg.get("ai.providers.custom.api_key", ""))
        self.wechat_enabled.setChecked(cfg.get("chat_reader.wechat.enabled", False))
        self.qq_enabled.setChecked(cfg.get("chat_reader.qq.enabled", False))
        self.napcat_url.setText(cfg.get("chat_reader.qq.napcat_url", "http://127.0.0.1:3000"))

    def _on_save(self) -> None:
        if not self.app or not self.app.config:
            return
        cfg = self.app.config
        cfg.set("ai.providers.openai.api_key", self.openai_key.text())
        cfg.set("ai.providers.anthropic.api_key", self.anthropic_key.text())
        cfg.set("ai.providers.ollama.base_url", self.ollama_url.text())
        cfg.set("ai.providers.custom.base_url", self.custom_url.text())
        cfg.set("ai.providers.custom.api_key", self.custom_key.text())
        cfg.set("chat_reader.wechat.enabled", self.wechat_enabled.isChecked())
        cfg.set("chat_reader.qq.enabled", self.qq_enabled.isChecked())
        cfg.set("chat_reader.qq.napcat_url", self.napcat_url.text())
        cfg.save()
