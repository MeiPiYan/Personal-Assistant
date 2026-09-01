"""Knowledge base panel."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QScrollArea, QComboBox, QFrame,
)


class KnowledgePanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("知识库")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # Add item row
        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("标题...")
        add_row.addWidget(self.title_input, 1)

        self.category_combo = QComboBox()
        self.category_combo.addItems(["全部", "技术", "工作", "生活", "学习", "其他"])
        self.category_combo.setFixedWidth(80)
        add_row.addWidget(self.category_combo)

        self.add_btn = QPushButton("添加")
        self.add_btn.setFixedWidth(64)
        self.add_btn.clicked.connect(self._on_add)
        add_row.addWidget(self.add_btn)

        layout.addLayout(add_row)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("粘贴要保存的内容...")
        self.content_input.setMaximumHeight(100)
        layout.addWidget(self.content_input)

        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索知识库...")
        search_row.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("搜索")
        self.search_btn.setFixedWidth(64)
        search_row.addWidget(self.search_btn)

        layout.addLayout(search_row)

        # Browse area
        self.browse_area = QScrollArea()
        self.browse_area.setWidgetResizable(True)
        self.browse_area.setFrameShape(QFrame.NoFrame)
        self.browse_container = QWidget()
        self.browse_layout = QVBoxLayout(self.browse_container)
        self.browse_layout.setAlignment(Qt.AlignTop)
        self.browse_area.setWidget(self.browse_container)
        layout.addWidget(self.browse_area, 1)

    def _on_add(self) -> None:
        title = self.title_input.text().strip()
        content = self.content_input.toPlainText().strip()
        if not content:
            return
        self.title_input.clear()
        self.content_input.clear()
