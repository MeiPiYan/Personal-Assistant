from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QComboBox, QLineEdit,
)


class DiaryPanel(QWidget):
    """Diary and notes panel with AI assistance."""

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("日记 / 笔记")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 0;")
        layout.addWidget(header)

        # New entry area
        entry_label = QLabel("写点什么...")
        layout.addWidget(entry_label)
        self.entry_input = QTextEdit()
        self.entry_input.setPlaceholderText("记录今天的事项、想法、感受...")
        self.entry_input.setMaximumHeight(150)
        layout.addWidget(self.entry_input)

        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(self.save_btn)

        self.ai_assist_btn = QPushButton("AI 润色")
        self.ai_assist_btn.clicked.connect(self._on_ai_assist)
        btn_layout.addWidget(self.ai_assist_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # History browser
        history_label = QLabel("历史记录")
        layout.addWidget(history_label)

        filter_layout = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("按标签或内容筛选...")
        filter_layout.addWidget(self.filter_input)
        self.filter_btn = QPushButton("筛选")
        filter_layout.addWidget(self.filter_btn)
        layout.addLayout(filter_layout)

        self.history_area = QScrollArea()
        self.history_area.setWidgetResizable(True)
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignTop)
        self.history_area.setWidget(self.history_container)
        layout.addWidget(self.history_area)

    def _on_save(self) -> None:
        content = self.entry_input.toPlainText().strip()
        if not content:
            return
        # Save to database
        self.entry_input.clear()

    def _on_ai_assist(self) -> None:
        content = self.entry_input.toPlainText().strip()
        if not content:
            return
        # AI polish and tag
