"""Search panel - web search and local knowledge base search."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QScrollArea, QFrame,
)


class SearchPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("搜索")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # Search input row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入搜索关键词...")
        self.search_input.returnPressed.connect(self._on_search)
        search_row.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedWidth(80)
        self.search_btn.clicked.connect(self._on_search)
        search_row.addWidget(self.search_btn)

        self.local_btn = QPushButton("本地")
        self.local_btn.setObjectName("secondaryBtn")
        self.local_btn.setFixedWidth(64)
        self.local_btn.clicked.connect(self._on_local_search)
        search_row.addWidget(self.local_btn)

        layout.addLayout(search_row)

        # Results area
        self.results_area = QScrollArea()
        self.results_area.setWidgetResizable(True)
        self.results_area.setFrameShape(QFrame.NoFrame)
        self.results_container = QWidget()
        self.results_layout = QVBoxLayout(self.results_container)
        self.results_layout.setAlignment(Qt.AlignTop)
        self.results_layout.setSpacing(8)
        self.results_area.setWidget(self.results_container)
        layout.addWidget(self.results_area, 1)

        # AI synthesis
        self.synthesis = QTextEdit()
        self.synthesis.setReadOnly(True)
        self.synthesis.setPlaceholderText("AI 综合分析结果将在此显示...")
        self.synthesis.setMaximumHeight(160)
        layout.addWidget(self.synthesis)

    def _on_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return
        self.synthesis.setPlainText("正在搜索...")

    def _on_local_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            return
        self.synthesis.setPlainText("正在搜索本地知识库...")
