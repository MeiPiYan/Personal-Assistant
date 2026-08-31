from __future__ import annotations

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QStatusBar,
    QLabel,
)

from .chat_panel import ChatPanel
from .document_panel import DocumentPanel
from .search_panel import SearchPanel
from .diary_panel import DiaryPanel
from .knowledge_panel import KnowledgePanel
from .settings_panel import SettingsPanel
from .chat_reader_panel import ChatReaderPanel


class MainWindow(QMainWindow):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.setWindowTitle("AI Assistant")
        self.setMinimumSize(800, 600)

        cfg = app.config if app else None
        w = cfg.get("ui.main_window.width", 900) if cfg else 900
        h = cfg.get("ui.main_window.height", 650) if cfg else 650
        self.resize(w, h)

        self._setup_ui()
        self._setup_status_bar()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.tabs.setDocumentMode(True)

        self.chat_panel = ChatPanel(app=self.app)
        self.doc_panel = DocumentPanel(app=self.app)
        self.search_panel = SearchPanel(app=self.app)
        self.diary_panel = DiaryPanel(app=self.app)
        self.knowledge_panel = KnowledgePanel(app=self.app)
        self.settings_panel = SettingsPanel(app=self.app)
        self.reader_panel = ChatReaderPanel(app=self.app)

        self.tabs.addTab(self.chat_panel, "AI 对话")
        self.tabs.addTab(self.doc_panel, "文档总结")
        self.tabs.addTab(self.search_panel, "搜索")
        self.tabs.addTab(self.reader_panel, "消息监控")
        self.tabs.addTab(self.diary_panel, "日记")
        self.tabs.addTab(self.knowledge_panel, "知识库")
        self.tabs.addTab(self.settings_panel, "设置")

        layout.addWidget(self.tabs)

    def _setup_status_bar(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("就绪")

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
