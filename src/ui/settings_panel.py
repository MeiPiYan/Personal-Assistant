"""Settings panel for API keys and configuration."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QFormLayout,
    QCheckBox, QScrollArea, QFrame, QRadioButton,
    QButtonGroup, QStackedWidget, QComboBox,
)

from ..ai.models import (
    CLOUD_PROVIDERS, PROVIDER_NAMES, PROVIDER_MODELS,
    get_provider_models_for_combo,
)


class SettingsPanel(QWidget):
    # Signal emitted when settings are saved
    settings_saved = Signal()

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

        # AI Provider - Hierarchical
        ai_group = QGroupBox("AI 模型配置")
        ai_layout = QVBoxLayout()

        # Provider type selector
        type_label = QLabel("选择模型来源:")
        type_label.setStyleSheet("color: #8888a0; font-size: 12px;")
        ai_layout.addWidget(type_label)

        self._type_group = QButtonGroup(self)
        self._type_group.setExclusive(True)

        type_row = QHBoxLayout()
        type_row.setSpacing(20)

        self.radio_cloud = QRadioButton("云端 API")
        self.radio_cloud.setToolTip("OpenAI、Anthropic 等云端服务")
        self._type_group.addButton(self.radio_cloud, 0)
        type_row.addWidget(self.radio_cloud)

        self.radio_local = QRadioButton("本地模型")
        self.radio_local.setToolTip("Ollama 等本地部署的模型")
        self._type_group.addButton(self.radio_local, 1)
        type_row.addWidget(self.radio_local)

        self.radio_custom = QRadioButton("自定义端点")
        self.radio_custom.setToolTip("任意 OpenAI 兼容的 API")
        self._type_group.addButton(self.radio_custom, 2)
        type_row.addWidget(self.radio_custom)

        type_row.addStretch()
        ai_layout.addLayout(type_row)

        # Stacked widget for different provider configs
        self._config_stack = QStackedWidget()

        # Page 0: Cloud API
        cloud_widget = QWidget()
        cloud_layout = QVBoxLayout(cloud_widget)
        cloud_layout.setContentsMargins(0, 12, 0, 0)
        cloud_layout.setSpacing(12)

        cloud_hint = QLabel("选择服务商并填入 API Key:")
        cloud_hint.setStyleSheet("color: #8888a0; font-size: 12px;")
        cloud_layout.addWidget(cloud_hint)

        # Provider selector
        provider_row = QHBoxLayout()
        provider_row.setSpacing(8)

        provider_label = QLabel("服务商:")
        provider_row.addWidget(provider_label)

        self.cloud_provider_combo = QComboBox()
        self.cloud_provider_combo.setFixedWidth(180)
        self.cloud_provider_combo.addItems([
            "OpenAI",
            "DeepSeek",
            "SiliconFlow",
            "Anthropic",
            "Google Gemini",
            "Groq",
        ])
        self.cloud_provider_combo.currentIndexChanged.connect(self._on_cloud_provider_changed)
        provider_row.addWidget(self.cloud_provider_combo)

        provider_row.addStretch()
        cloud_layout.addLayout(provider_row)

        # Provider config stack
        self._provider_stack = QStackedWidget()

        # Helper to create provider config widgets
        self._provider_configs = {}

        for provider in CLOUD_PROVIDERS:
            widget = QWidget()
            form = QFormLayout(widget)
            form.setContentsMargins(0, 0, 0, 0)

            # API Key
            key_input = QLineEdit()
            key_input.setEchoMode(QLineEdit.Password)
            key_input.setMinimumWidth(320)
            if provider == "anthropic":
                key_input.setPlaceholderText("sk-ant-...")
            elif provider == "groq":
                key_input.setPlaceholderText("gsk_...")
            elif provider == "gemini":
                key_input.setPlaceholderText("AIza...")
            else:
                key_input.setPlaceholderText("sk-...")
            form.addRow("API Key:", key_input)

            # Model combo
            model_combo = QComboBox()
            model_combo.setEditable(True)
            model_combo.setFixedWidth(280)
            for model_id, display_name, _ in PROVIDER_MODELS.get(provider, []):
                model_combo.addItem(display_name, model_id)
            form.addRow("默认模型:", model_combo)

            # Hint for special providers
            if provider == "siliconflow":
                hint = QLabel("* SiliconFlow 聚合多家模型，按用量计费，性价比高")
                hint.setStyleSheet("color: #8888a0; font-size: 11px;")
                form.addRow("", hint)
            elif provider == "groq":
                hint = QLabel("* Groq 提供免费额度，推理速度极快")
                hint.setStyleSheet("color: #8888a0; font-size: 11px;")
                form.addRow("", hint)

            self._provider_configs[provider] = {
                "key_input": key_input,
                "model_combo": model_combo,
            }
            self._provider_stack.addWidget(widget)

        cloud_layout.addWidget(self._provider_stack)
        cloud_layout.addStretch()

        self._config_stack.addWidget(cloud_widget)

        # Page 1: Local model (Ollama)
        local_widget = QWidget()
        local_layout = QVBoxLayout(local_widget)
        local_layout.setContentsMargins(0, 12, 0, 0)
        local_layout.setSpacing(12)

        local_hint = QLabel("配置本地 Ollama 服务:")
        local_hint.setStyleSheet("color: #8888a0; font-size: 12px;")
        local_layout.addWidget(local_hint)

        local_form = QFormLayout()
        local_form.setContentsMargins(0, 0, 0, 0)

        self.ollama_url = QLineEdit()
        self.ollama_url.setText("http://localhost:11434")
        self.ollama_url.setMinimumWidth(320)
        local_form.addRow("Ollama 地址:", self.ollama_url)

        self.ollama_model = QComboBox()
        self.ollama_model.setEditable(True)
        self.ollama_model.addItems([
            "llama3.1",
            "llama3.1:8b",
            "llama3.1:70b",
            "mistral",
            "codellama",
            "qwen2.5",
            "deepseek-coder-v2",
        ])
        self.ollama_model.setFixedWidth(200)
        local_form.addRow("默认模型:", self.ollama_model)

        local_layout.addLayout(local_form)

        # Ollama status
        self.ollama_status = QLabel("")
        self.ollama_status.setStyleSheet("color: #8888a0; font-size: 11px;")
        local_layout.addWidget(self.ollama_status)

        local_layout.addStretch()

        self._config_stack.addWidget(local_widget)

        # Page 2: Custom endpoint
        custom_widget = QWidget()
        custom_layout = QVBoxLayout(custom_widget)
        custom_layout.setContentsMargins(0, 12, 0, 0)
        custom_layout.setSpacing(12)

        custom_hint = QLabel("配置 OpenAI 兼容的自定义 API 端点:")
        custom_hint.setStyleSheet("color: #8888a0; font-size: 12px;")
        custom_layout.addWidget(custom_hint)

        custom_form = QFormLayout()
        custom_form.setContentsMargins(0, 0, 0, 0)

        self.custom_url = QLineEdit()
        self.custom_url.setPlaceholderText("http://localhost:8000/v1")
        self.custom_url.setMinimumWidth(320)
        custom_form.addRow("API 地址:", self.custom_url)

        self.custom_key = QLineEdit()
        self.custom_key.setEchoMode(QLineEdit.Password)
        self.custom_key.setPlaceholderText("留空或填入 Key")
        self.custom_key.setMinimumWidth(320)
        custom_form.addRow("API Key:", self.custom_key)

        self.custom_model = QComboBox()
        self.custom_model.setEditable(True)
        self.custom_model.setPlaceholderText("输入模型名称")
        self.custom_model.setFixedWidth(200)
        custom_form.addRow("默认模型:", self.custom_model)

        custom_layout.addLayout(custom_form)
        custom_layout.addStretch()

        self._config_stack.addWidget(custom_widget)

        ai_layout.addWidget(self._config_stack)

        # Advanced options (collapsed)
        self.advanced_toggle = QCheckBox("显示高级选项")
        self.advanced_toggle.stateChanged.connect(self._on_advanced_toggled)
        ai_layout.addWidget(self.advanced_toggle)

        self._advanced_widget = QWidget()
        advanced_form = QFormLayout(self._advanced_widget)
        advanced_form.setContentsMargins(0, 4, 0, 0)

        from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox

        self.max_tokens = QSpinBox()
        self.max_tokens.setRange(256, 128000)
        self.max_tokens.setValue(4096)
        self.max_tokens.setSuffix(" tokens")
        advanced_form.addRow("最大 Token:", self.max_tokens)

        self.temperature = QDoubleSpinBox()
        self.temperature.setRange(0.0, 2.0)
        self.temperature.setSingleStep(0.1)
        self.temperature.setValue(0.7)
        advanced_form.addRow("Temperature:", self.temperature)

        self._advanced_widget.hide()
        ai_layout.addWidget(self._advanced_widget)

        ai_group.setLayout(ai_layout)
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

        # Connect radio buttons
        self._type_group.idClicked.connect(self._on_type_changed)

        self._load_settings()

    def _on_type_changed(self, type_id: int) -> None:
        self._config_stack.setCurrentIndex(type_id)

    def _on_cloud_provider_changed(self, index: int) -> None:
        self._provider_stack.setCurrentIndex(index)

    def _on_advanced_toggled(self, state: int) -> None:
        self._advanced_widget.setVisible(state == Qt.Checked)

    def _load_settings(self) -> None:
        if not self.app or not self.app.config:
            return
        cfg = self.app.config

        # Determine provider type
        provider = cfg.get("ai.default_provider", "deepseek")
        if provider in CLOUD_PROVIDERS:
            self.radio_cloud.setChecked(True)
            self._config_stack.setCurrentIndex(0)
            # Set cloud provider index
            idx = CLOUD_PROVIDERS.index(provider)
            self.cloud_provider_combo.setCurrentIndex(idx)
            self._on_cloud_provider_changed(idx)
        elif provider == "ollama":
            self.radio_local.setChecked(True)
            self._config_stack.setCurrentIndex(1)
        else:
            self.radio_custom.setChecked(True)
            self._config_stack.setCurrentIndex(2)

        # Load cloud provider values
        for p in CLOUD_PROVIDERS:
            config = self._provider_configs.get(p)
            if config:
                api_key = cfg.get(f"ai.providers.{p}.api_key", "")
                model_id = cfg.get(f"ai.providers.{p}.model", "")

                config["key_input"].setText(api_key)

                # Find and set model
                if model_id:
                    idx = config["model_combo"].findData(model_id)
                    if idx >= 0:
                        config["model_combo"].setCurrentIndex(idx)
                    else:
                        config["model_combo"].setEditText(model_id)

        # Load local values
        self.ollama_url.setText(cfg.get("ai.providers.ollama.base_url", "http://localhost:11434"))
        ollama_model = cfg.get("ai.providers.ollama.model", "llama3.1")
        idx = self.ollama_model.findData(ollama_model)
        if idx >= 0:
            self.ollama_model.setCurrentIndex(idx)
        else:
            self.ollama_model.setEditText(ollama_model)

        # Load custom values
        self.custom_url.setText(cfg.get("ai.providers.custom.base_url", ""))
        self.custom_key.setText(cfg.get("ai.providers.custom.api_key", ""))
        self.custom_model.setCurrentText(cfg.get("ai.providers.custom.model", ""))

        # Advanced
        self.max_tokens.setValue(cfg.get("ai.max_tokens", 4096))
        self.temperature.setValue(cfg.get("ai.temperature", 0.7))

        # Chat reader
        self.wechat_enabled.setChecked(cfg.get("chat_reader.wechat.enabled", False))
        self.qq_enabled.setChecked(cfg.get("chat_reader.qq.enabled", False))
        self.napcat_url.setText(cfg.get("chat_reader.qq.napcat_url", "http://127.0.0.1:3000"))

    def _on_save(self) -> None:
        if not self.app or not self.app.config:
            return
        cfg = self.app.config

        # Determine selected provider
        type_id = self._type_group.checkedId()
        if type_id == 0:  # Cloud
            provider_idx = self.cloud_provider_combo.currentIndex()
            provider = CLOUD_PROVIDERS[provider_idx]

            # Save the selected provider's config
            config = self._provider_configs.get(provider)
            if config:
                api_key = config["key_input"].text()
                model_id = config["model_combo"].currentData()
                if not model_id:
                    model_id = config["model_combo"].currentText()

                cfg.set(f"ai.providers.{provider}.api_key", api_key)
                cfg.set(f"ai.providers.{provider}.model", model_id)

        elif type_id == 1:  # Local
            provider = "ollama"
            cfg.set("ai.providers.ollama.base_url", self.ollama_url.text())
            model_id = self.ollama_model.currentData()
            if not model_id:
                model_id = self.ollama_model.currentText()
            cfg.set("ai.providers.ollama.model", model_id)
        else:  # Custom
            provider = "custom"
            cfg.set("ai.providers.custom.base_url", self.custom_url.text())
            cfg.set("ai.providers.custom.api_key", self.custom_key.text())
            cfg.set("ai.providers.custom.model", self.custom_model.currentText())

        cfg.set("ai.default_provider", provider)

        # Also save the model to default_model for chat panel
        if type_id == 0:
            config = self._provider_configs.get(provider)
            if config:
                model_id = config["model_combo"].currentData()
                if not model_id:
                    model_id = config["model_combo"].currentText()
                cfg.set("ai.default_model", model_id)
        elif type_id == 1:
            model_id = self.ollama_model.currentData()
            if not model_id:
                model_id = self.ollama_model.currentText()
            cfg.set("ai.default_model", model_id)

        cfg.set("ai.max_tokens", self.max_tokens.value())
        cfg.set("ai.temperature", self.temperature.value())

        # Chat reader
        cfg.set("chat_reader.wechat.enabled", self.wechat_enabled.isChecked())
        cfg.set("chat_reader.qq.enabled", self.qq_enabled.isChecked())
        cfg.set("chat_reader.qq.napcat_url", self.napcat_url.text())

        cfg.save()

        # Emit signal to update chat panel
        self.settings_saved.emit()
