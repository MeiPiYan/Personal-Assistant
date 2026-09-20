"""Document panel - file parsing and AI summarization."""
from __future__ import annotations

import asyncio

from src.ui.tasks import spawn_ui

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QPushButton, QFrame, QSplitter, QLineEdit,
)

from .widgets.file_drop import FileDropWidget
from ..document.summarizer import DocumentSummarizer


class DocumentPanel(QWidget):
    def __init__(self, app=None, parent=None):
        super().__init__(parent)
        self.app = app
        self._current_text = ""
        self._ai_engine = None
        self._summarizer: DocumentSummarizer | None = None
        self._vector_store = None  # set via set_vector_store (P1)
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

        self.index_btn = QPushButton("存入知识库")
        self.index_btn.setObjectName("secondaryBtn")
        self.index_btn.setEnabled(False)
        self.index_btn.clicked.connect(self._on_index)
        btn_row.addWidget(self.index_btn)

        btn_row.addStretch()
        right_layout.addLayout(btn_row)

        self.summary_output = QTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setPlaceholderText("总结结果...")
        right_layout.addWidget(self.summary_output)
        splitter.addWidget(right)

        splitter.setSizes([200, 200])
        layout.addWidget(splitter, 1)

    def set_ai_engine(self, engine) -> None:
        """Receive the shared AI engine and create the summarizer."""
        self._ai_engine = engine
        self._summarizer = DocumentSummarizer(ai_engine=engine)

    def set_vector_store(self, store) -> None:
        """Receive the shared vector store so parsed docs can be indexed (P1)."""
        self._vector_store = store

    def _on_files_dropped(self, files: list[str]) -> None:
        spawn_ui(self._parse_files(files))

    async def _parse_files(self, files: list[str]) -> None:
        from src.document.parser import DocumentParser
        parser = DocumentParser()
        # Parsing large PDFs blocks for seconds, so run it off the UI thread.
        loop = asyncio.get_event_loop()
        texts = []
        for f in files:
            text = await loop.run_in_executor(None, parser.parse, f)
            if text:
                texts.append(f"--- {f} ---\n{text}")
                await self._index_document(text, title=f, source_path=f)
        self._current_text = "\n\n".join(texts)
        self.content_preview.setPlainText(self._current_text[:5000])
        self.summarize_btn.setEnabled(bool(self._current_text))
        self.index_btn.setEnabled(bool(self._current_text))

    def _on_fetch_url(self) -> None:
        url = self.url_input.text().strip()
        if not url:
            return
        spawn_ui(self._fetch_url(url))

    async def _fetch_url(self, url: str) -> None:
        import trafilatura
        # Fetching a remote page can block for tens of seconds.
        loop = asyncio.get_event_loop()
        downloaded = await loop.run_in_executor(None, trafilatura.fetch_url, url)
        if downloaded:
            self._current_text = trafilatura.extract(downloaded) or ""
            self.content_preview.setPlainText(self._current_text[:5000])
            self.summarize_btn.setEnabled(bool(self._current_text))
            self.index_btn.setEnabled(bool(self._current_text))
            await self._index_document(
                self._current_text, title=url, source_path=url, source_type="html"
            )

    # -- Vector knowledge base (P1) ------------------------------------------ #

    async def _index_document(self, text: str, title: str = "",
                              source_path: str = "",
                              source_type: str = "document") -> bool:
        """Index parsed document text into the vector knowledge base."""
        if not text or self._vector_store is None:
            return False
        try:
            res = await self._vector_store.index_text(
                text, title=title or source_path,
                source_path=source_path, source_type=source_type,
            )
            return res.get("chunks", 0) > 0
        except Exception:
            return False

    def _on_index(self) -> None:
        if not self._current_text:
            return
        spawn_ui(self._do_index())

    async def _do_index(self) -> None:
        title = self.url_input.text().strip() or "手动文档"
        ok = await self._index_document(self._current_text, title=title)
        self.summary_output.setPlainText(
            "已存入知识库（已建立向量索引）" if ok
            else "存入知识库失败或无可索引内容"
        )

    def _on_summarize(self) -> None:
        if not self._current_text or not self._summarizer:
            return
        # Show loading state
        self.summarize_btn.setEnabled(False)
        self.summarize_btn.setText("总结中...")
        self.summary_output.setPlainText("正在生成总结，请稍候...")
        # Schedule the async summarization
        spawn_ui(self._do_summarize())

    async def _do_summarize(self) -> None:
        try:
            result = await self._summarizer.summarize(self._current_text)
            self.summary_output.setPlainText(result)
        except Exception as e:
            self.summary_output.setPlainText(f"[总结失败: {e}]")
        finally:
            self.summarize_btn.setEnabled(True)
            self.summarize_btn.setText("生成总结")
