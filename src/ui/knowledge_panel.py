from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QScrollArea, QComboBox,
)


class KnowledgePanel(QWidget):
    """Knowledge base browser and clip manager."""

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        header = QLabel("知识库")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 0;")
        layout.addWidget(header)

        # Add new item
        add_layout = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("标题...")
        add_layout.addWidget(self.title_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部", "技术", "工作", "生活", "学习", "其他"])
        add_layout.addWidget(self.category_combo)

        self.add_btn = QPushButton("添加剪藏")
        self.add_btn.clicked.connect(self._on_add)
        add_layout.addWidget(self.add_btn)
        layout.addLayout(add_layout)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("粘贴要保存的内容...")
        self.content_input.setMaximumHeight(100)
        layout.addWidget(self.content_input)

        # Browse area
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索知识库...")
        search_layout.addWidget(self.search_input)
        self.search_btn = QPushButton("搜索")
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)

        self.browse_area = QScrollArea()
        self.browse_area.setWidgetResizable(True)
        self.browse_container = QWidget()
        self.browse_layout = QVBoxLayout(self.browse_container)
        self.browse_layout.setAlignment(Qt.AlignTop)
        self.browse_area.setWidget(self.browse_container)
        layout.addWidget(self.browse_area)

    def _on_add(self) -> None:
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        if not content:
            return
        # Save to knowledge base
        self.title_input.clear()
        self.content_input.clear()
