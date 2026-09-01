"""Diary panel - notes with AI assistance."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QScrollArea, QLineEdit, QFrame,
)


class DiaryPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("日记 / 笔记")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # Entry input
        self.entry_input = QTextEdit()
        self.entry_input.setPlaceholderText("记录今天的事项、想法、感受...")
        self.entry_input.setMaximumHeight(140)
        layout.addWidget(self.entry_input)

        # Buttons
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self.save_btn)

        self.ai_assist_btn = QPushButton("AI 润色")
        self.ai_assist_btn.setObjectName("secondaryBtn")
        self.ai_assist_btn.clicked.connect(self._on_ai_assist)
        btn_row.addWidget(self.ai_assist_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #2a2a3e; max-height: 1px;")
        layout.addWidget(divider)

        # History
        history_label = QLabel("历史记录")
        history_label.setStyleSheet("color: #8888a0; font-size: 12px;")
        layout.addWidget(history_label)

        filter_row = QHBoxLayout()
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("按标签或内容筛选...")
        filter_row.addWidget(self.filter_input, 1)
        self.filter_btn = QPushButton("筛选")
        self.filter_btn.setObjectName("secondaryBtn")
        self.filter_btn.setFixedWidth(64)
        filter_row.addWidget(self.filter_btn)
        layout.addLayout(filter_row)

        self.history_area = QScrollArea()
        self.history_area.setWidgetResizable(True)
        self.history_area.setFrameShape(QFrame.NoFrame)
        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignTop)
        self.history_area.setWidget(self.history_container)
        layout.addWidget(self.history_area, 1)

    def _on_save(self) -> None:
        content = self.entry_input.toPlainText().strip()
        if not content:
            return
        self.entry_input.clear()

    def _on_ai_assist(self) -> None:
        content = self.entry_input.toPlainText().strip()
        if not content:
            return
