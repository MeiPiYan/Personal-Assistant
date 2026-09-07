"""Settings panel for API keys and configuration."""

from __future__ import annotations

import asyncio

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QGroupBox, QFormLayout,
    QCheckBox, QScrollArea, QFrame, QRadioButton,
    QButtonGroup, QStackedWidget, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
)

from .styles import ThemeManager
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
        self._backup_mgr = None
        self._setup_ui()
        ThemeManager.register_panel(self)

    def _apply_theme(self) -> None:
        c = ThemeManager.get_colors()
        self._type_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._cloud_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._local_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._ollama_status.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        self._custom_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._backup_dir_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._backup_dir_display.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._auto_interval_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._keep_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        self._backup_status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        self._table_header.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px; padding-top: 4px;"
        )
        # Refresh provider hint labels
        for hint in self._provider_hints:
            hint.setStyleSheet(f"color: {c.text_secondary}; font-size: 11px;")
        # Refresh restore buttons
        for row_idx in range(self.backup_table.rowCount()):
            btn = self.backup_table.cellWidget(row_idx, 4)
            if btn and isinstance(btn, QPushButton):
                btn.setStyleSheet(
                    f"QPushButton {{ background-color: {c.btn_secondary_bg}; color: {c.btn_secondary_text}; "
                    f"border: 1px solid {c.btn_secondary_border}; border-radius: 4px; padding: 2px 8px; }}"
                    f"QPushButton:hover {{ background-color: {c.btn_secondary_hover_bg}; color: {c.btn_secondary_hover_text}; }}"
                )

    def _setup_ui(self) -> None:
        c = ThemeManager.get_colors()
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

        # Appearance settings
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout()

        self.theme_combo = QComboBox()
        self.theme_combo.setFixedWidth(180)
        self.theme_combo.addItems(["深色", "浅色"])
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        appearance_layout.addRow("主题:", self.theme_combo)

        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)

        # AI Provider - Hierarchical
        ai_group = QGroupBox("AI 模型配置")
        ai_layout = QVBoxLayout()

        # Provider type selector
        self._type_label = QLabel("选择模型来源:")
        self._type_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        ai_layout.addWidget(self._type_label)

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

        self._cloud_hint = QLabel("选择服务商并填入 API Key:")
        self._cloud_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        cloud_layout.addWidget(self._cloud_hint)

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
        self._provider_hints = []

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
                hint.setStyleSheet(
                    f"color: {c.text_secondary}; font-size: 11px;"
                )
                self._provider_hints.append(hint)
                form.addRow("", hint)
            elif provider == "groq":
                hint = QLabel("* Groq 提供免费额度，推理速度极快")
                hint.setStyleSheet(
                    f"color: {c.text_secondary}; font-size: 11px;"
                )
                self._provider_hints.append(hint)
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

        self._local_hint = QLabel("配置本地 Ollama 服务:")
        self._local_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        local_layout.addWidget(self._local_hint)

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
        self._ollama_status = QLabel("")
        self._ollama_status.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        local_layout.addWidget(self._ollama_status)

        local_layout.addStretch()

        self._config_stack.addWidget(local_widget)

        # Page 2: Custom endpoint
        custom_widget = QWidget()
        custom_layout = QVBoxLayout(custom_widget)
        custom_layout.setContentsMargins(0, 12, 0, 0)
        custom_layout.setSpacing(12)

        self._custom_hint = QLabel("配置 OpenAI 兼容的自定义 API 端点:")
        self._custom_hint.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        custom_layout.addWidget(self._custom_hint)

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

        # --- Backup Section ---
        backup_group = QGroupBox("备份管理")
        backup_layout = QVBoxLayout()
        backup_layout.setSpacing(10)

        # Backup controls row
        backup_ctrl_row = QHBoxLayout()

        self.backup_enabled_check = QCheckBox("启用自动备份")
        backup_ctrl_row.addWidget(self.backup_enabled_check)

        backup_ctrl_row.addSpacing(16)

        self._backup_dir_label = QLabel("备份目录:")
        self._backup_dir_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        backup_ctrl_row.addWidget(self._backup_dir_label)

        self.backup_dir_display = QLineEdit()
        self.backup_dir_display.setReadOnly(True)
        self.backup_dir_display.setFixedWidth(200)
        self.backup_dir_display.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        backup_ctrl_row.addWidget(self.backup_dir_display)

        self.backup_now_btn = QPushButton("立即备份")
        self.backup_now_btn.clicked.connect(self._on_backup_now)
        backup_ctrl_row.addWidget(self.backup_now_btn)

        backup_ctrl_row.addStretch()
        backup_layout.addLayout(backup_ctrl_row)

        # Auto-backup settings row
        auto_row = QHBoxLayout()

        self._auto_interval_label = QLabel("自动备份间隔 (小时):")
        self._auto_interval_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        auto_row.addWidget(self._auto_interval_label)

        from PySide6.QtWidgets import QSpinBox
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 720)
        self.backup_interval_spin.setValue(24)
        self.backup_interval_spin.setSuffix(" h")
        self.backup_interval_spin.setFixedWidth(80)
        auto_row.addWidget(self.backup_interval_spin)

        auto_row.addSpacing(16)

        self._keep_label = QLabel("保留备份数:")
        self._keep_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px;"
        )
        auto_row.addWidget(self._keep_label)

        self.backup_keep_spin = QSpinBox()
        self.backup_keep_spin.setRange(1, 100)
        self.backup_keep_spin.setValue(10)
        self.backup_keep_spin.setFixedWidth(60)
        auto_row.addWidget(self.backup_keep_spin)

        self.cleanup_btn = QPushButton("清理旧备份")
        self.cleanup_btn.clicked.connect(self._on_cleanup_backups)
        auto_row.addWidget(self.cleanup_btn)

        auto_row.addStretch()
        backup_layout.addLayout(auto_row)

        # Backup status label
        self._backup_status_label = QLabel("")
        self._backup_status_label.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 11px;"
        )
        backup_layout.addWidget(self._backup_status_label)

        # Recent backups table
        self._table_header = QLabel("最近备份:")
        self._table_header.setStyleSheet(
            f"color: {c.text_secondary}; font-size: 12px; padding-top: 4px;"
        )
        backup_layout.addWidget(self._table_header)

        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(5)
        self.backup_table.setHorizontalHeaderLabels(["类型", "时间", "大小", "文件名", "操作"])
        self.backup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.backup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.backup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.backup_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.backup_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.backup_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.backup_table.verticalHeader().setVisible(False)
        self.backup_table.setMaximumHeight(200)
        backup_layout.addWidget(self.backup_table)

        # Refresh button
        refresh_row = QHBoxLayout()
        refresh_row.addStretch()
        self.refresh_backups_btn = QPushButton("刷新列表")
        self.refresh_backups_btn.clicked.connect(self._load_backup_list)
        refresh_row.addWidget(self.refresh_backups_btn)
        backup_layout.addLayout(refresh_row)

        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)

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

    def _on_theme_changed(self, index: int) -> None:
        """Apply theme immediately when combo changes."""
        theme = "dark" if index == 0 else "light"
        ThemeManager.apply(theme)

    def _load_settings(self) -> None:
        if not self.app or not self.app.config:
            return
        cfg = self.app.config

        # Load theme preference
        theme = cfg.get("ui.theme", "dark")
        theme_index = 0 if theme == "dark" else 1
        # Block signals to avoid triggering apply during load
        self.theme_combo.blockSignals(True)
        self.theme_combo.setCurrentIndex(theme_index)
        self.theme_combo.blockSignals(False)

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

        # Save theme preference
        theme = "dark" if self.theme_combo.currentIndex() == 0 else "light"
        cfg.set("ui.theme", theme)

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

        # Save backup settings
        cfg.set("backup.enabled", self.backup_enabled_check.isChecked())
        cfg.set("backup.interval_hours", self.backup_interval_spin.value())
        cfg.set("backup.max_backups", self.backup_keep_spin.value())

        # Emit signal to update chat panel
        self.settings_saved.emit()

    # --- Backup Methods ---

    def set_backup_manager(self, backup_mgr) -> None:
        """Receive the BackupManager instance."""
        self._backup_mgr = backup_mgr
        self._load_backup_settings()
        self._load_backup_list()

    def _load_backup_settings(self) -> None:
        """Load backup settings from config into UI."""
        if not self.app or not self.app.config:
            return
        cfg = self.app.config

        self.backup_enabled_check.setChecked(cfg.get("backup.enabled", True))
        self.backup_interval_spin.setValue(cfg.get("backup.interval_hours", 24))
        self.backup_keep_spin.setValue(cfg.get("backup.max_backups", 10))
        self.backup_dir_display.setText(cfg.get("backup.directory", "data/backups"))

    def _on_backup_now(self) -> None:
        """Trigger immediate backup of both database and config."""
        if not self._backup_mgr:
            self._backup_status_label.setText("备份管理器未初始化")
            return

        self.backup_now_btn.setEnabled(False)
        self._backup_status_label.setText("正在备份...")

        async def do_backup():
            try:
                result = await self._backup_mgr.backup_all()
                db_ok = result.get("database", {}).get("success", False)
                cfg_ok = result.get("config", {}).get("success", False)

                if db_ok and cfg_ok:
                    self._backup_status_label.setText("备份完成 ✓")
                elif db_ok:
                    self._backup_status_label.setText(
                        f"数据库备份成功，配置备份失败: {result.get('config', {}).get('error', '')}"
                    )
                elif cfg_ok:
                    self._backup_status_label.setText(
                        f"配置备份成功，数据库备份失败: {result.get('database', {}).get('error', '')}"
                    )
                else:
                    self._backup_status_label.setText(
                        f"备份失败: {result.get('database', {}).get('error', '未知错误')}"
                    )

                # Also do cleanup
                await self._backup_mgr.cleanup_old_backups()

                # Refresh the list
                self._load_backup_list()
            except Exception as e:
                self._backup_status_label.setText(f"备份出错: {e}")
            finally:
                self.backup_now_btn.setEnabled(True)

        asyncio.ensure_future(do_backup())

    def _on_cleanup_backups(self) -> None:
        """Clean up old backups beyond the configured keep count."""
        if not self._backup_mgr:
            return

        async def do_cleanup():
            try:
                keep = self.backup_keep_spin.value()
                result = await self._backup_mgr.cleanup_old_backups(keep_count=keep)
                removed = result.get("removed", 0)
                self._backup_status_label.setText(f"已清理 {removed} 个旧备份")
                self._load_backup_list()
            except Exception as e:
                self._backup_status_label.setText(f"清理出错: {e}")

        asyncio.ensure_future(do_cleanup())

    def _load_backup_list(self) -> None:
        """Load and display the list of available backups."""
        if not self._backup_mgr:
            return

        c = ThemeManager.get_colors()
        backups = self._backup_mgr.list_backups()
        self.backup_table.setRowCount(len(backups))

        for row, bk in enumerate(backups):
            # Type
            type_text = "数据库" if bk["type"] == "database" else "配置"
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignCenter)
            self.backup_table.setItem(row, 0, type_item)

            # Time
            time_item = QTableWidgetItem(bk["display_time"])
            time_item.setTextAlignment(Qt.AlignCenter)
            self.backup_table.setItem(row, 1, time_item)

            # Size
            size_item = QTableWidgetItem(bk["size_formatted"])
            size_item.setTextAlignment(Qt.AlignCenter)
            self.backup_table.setItem(row, 2, size_item)

            # Filename
            self.backup_table.setItem(row, 3, QTableWidgetItem(bk["filename"]))

            # Restore button
            restore_btn = QPushButton("恢复")
            restore_btn.setFixedWidth(60)
            restore_btn.setStyleSheet(
                f"QPushButton {{ background-color: {c.btn_secondary_bg}; color: {c.btn_secondary_text}; "
                f"border: 1px solid {c.btn_secondary_border}; border-radius: 4px; padding: 2px 8px; }}"
                f"QPushButton:hover {{ background-color: {c.btn_secondary_hover_bg}; color: {c.btn_secondary_hover_text}; }}"
            )
            restore_btn.clicked.connect(
                lambda checked, path=bk["path"], btype=bk["type"]: self._on_restore(path, btype)
            )
            self.backup_table.setCellWidget(row, 4, restore_btn)

    def _on_restore(self, backup_path: str, backup_type: str) -> None:
        """Restore from a specific backup with confirmation."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("确认恢复")
        msg.setText(f"确定要从此备份恢复{'数据库' if backup_type == 'database' else '配置文件'}吗？")
        msg.setInformativeText("当前文件将在恢复前自动备份。")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg.setDefaultButton(QMessageBox.Cancel)

        if msg.exec() != QMessageBox.Ok:
            return

        self._backup_status_label.setText("正在恢复...")

        async def do_restore():
            try:
                if backup_type == "database":
                    result = await self._backup_mgr.restore_database(backup_path)
                else:
                    result = await self._backup_mgr.restore_config(backup_path)

                if result.get("success"):
                    self._backup_status_label.setText(result["message"] + " ✓")
                else:
                    self._backup_status_label.setText(f"恢复失败: {result.get('error', '')}")

                self._load_backup_list()
            except Exception as e:
                self._backup_status_label.setText(f"恢复出错: {e}")

        asyncio.ensure_future(do_restore())
