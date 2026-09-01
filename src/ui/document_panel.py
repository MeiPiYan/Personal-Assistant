"""Document panel - file parsing and AI summarization."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFrame, QSplitter, QLineEdit,
)

from .widgets.file_drop import FileDropWidget


class DocumentPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._current_text = ""
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        header = QLabel("文档解析")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 0 0 4px 0;")
        layout.addWidget(header)

        # Drop area
        self.drop_widget = FileDropWidget()
        self.drop_widget.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_widget)

        # URL input row
        url_row = QHBoxLayout()
        url_row.setSpacing(8)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("或粘贴网页 URL...")
        url_row.addWidget(self.url_input, 1)

        fetch_btn = QPushButton("提取")
        fetch_btn.setFixedWidth(64)
        fetch_btn.clicked.connect(self._on_fetch_url)
        url_row.addWidget(fetch_btn)

        layout.addLayout(url_row)

        # Content + Summary splitter
        splitter = QSplitter(Qt.Vertical)

        # Content preview
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        left_layout.addWidget(QLabel("文档内容"))
        self.content_preview = QTextEdit()
        self.content_preview.setReadOnly(True)
        self.content_preview.setPlaceholderText("文档内容预览...")
        left_layout.addWidget(self.content_preview)
        splitter.addWidget(left)

        # Summary
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right_layout.addWidget(QLabel("AI 总结"))

        btn_row = QHBoxLayout()
        self.summarize_btn = QPushButton("生成总结")
        self.summarize_btn.setEnabled(False)
        self.summarize_btn.clicked.connect(self._on_summarize)
        btn_row.addWidget(self.summarize_btn)
        btn_row.addStretch()
        right_layout.addLayout(btn_row)

        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("总结结果...")
        right_layout.addWidget(self.summary_output)
        splitter.addWidget(right)

        splitter.setSizes([200, 200])
        layout.addWidget(splitter, 1)

    def _on_files_dropped(self, files: list[str]) -> None:
        from src.document.parser import DocumentParser
        parser = DocumentParser()
        texts = []
        for f in files:
            text = parser.parse(f)
            if text:
                texts.append(f"--- {f} ---\n{text}")
        self._current_text = "\n\n".join(texts)
        self.content_preview.setPlainText(self._current_text[:5000])
        self.summarize_btn.setEnabled(bool(self._current_text))

    def _on_fetch_url(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            return
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            self._current_text = trafilatura.extract(downloaded) or ""
            self.content_preview.setPlainText(self._current_text[:5000])
            self.summarize_btn.setEnabled(bool(self._current_text))

    def _on_summarize(self) -> None:
        if not self._current_text or not self.app:
            return
        self.summary_output.setPlainText("正在生成总结...")
