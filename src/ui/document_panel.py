from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFileDialog, QScrollArea, QFrame,
)

from .widgets.file_drop import FileDropWidget


class DocumentPanel(QWidget):
    """Document upload and AI summarization panel."""

    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        # Header
        header = QLabel("文档读取与总结")
        header.setStyleSheet("font-size: 18px; font-weight: bold; padding: 8px 0;")
        layout.addWidget(header)

        # File drop area
        self.drop_widget = FileDropWidget()
        self.drop_widget.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_widget)

        # Or paste URL
        url_layout = QHBoxLayout()
        self.url_input = QTextEdit()
        self.url_input.setMaximumHeight(36)
        self.url_input.setPlaceholderText("或粘贴网页 URL...")
        url_layout.addWidget(self.url_input)
        fetch_btn = QPushButton("提取")
        fetch_btn.setFixedWidth(80)
        fetch_btn.clicked.connect(self._on_fetch_url)
        url_layout.addWidget(fetch_btn)
        layout.addLayout(url_layout)

        # Content preview
        preview_label = QLabel("文档内容:")
        layout.addWidget(preview_label)
        self.content_preview = QTextEdit()
        self.content_preview.setReadOnly(True)
        self.content_preview.setMaximumHeight(200)
        layout.addWidget(self.content_preview)

        # Summary button + output
        btn_layout = QHBoxLayout()
        self.summarize_btn = QPushButton("AI 总结")
        self.summarize_btn.clicked.connect(self._on_summarize)
        self.summarize_btn.setEnabled(False)
        btn_layout.addWidget(self.summarize_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        summary_label = QLabel("AI 总结:")
        layout.addWidget(summary_label)
        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        layout.addWidget(self.summary_output)

        self._current_text = ""

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
        url = self.url_input.toPlainText().strip()
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
        # Will be connected to AI engine via panel coordination
