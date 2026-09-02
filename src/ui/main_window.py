"""Main window with sidebar navigation."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QFont, QPainter, QColor, QPixmap
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QStatusBar, QLabel, QButtonGroup,
    QPushButton, QFrame, QSizePolicy, QSpacerItem,
)

from .chat_panel import ChatPanel
from .document_panel import DocumentPanel
from .search_panel import SearchPanel
from .diary_panel import DiaryPanel
from .knowledge_panel import KnowledgePanel
from .settings_panel import SettingsPanel
from .chat_reader_panel import ChatReaderPanel


# Navigation items: (icon_char, label, tooltip)
_NAV_ITEMS = [
    ("💬", "对话", "AI 对话"),
    ("🔍", "搜索", "网络 / 本地搜索"),
    ("📄", "文档", "文档解析与总结"),
    ("📖", "监控", "聊天消息监控"),
    ("📝", "日记", "日记与笔记"),
    ("📚", "知识", "知识库"),
    ("⚙", "设置", "应用设置"),
]


def _make_nav_button(icon_text: str, label: str, tooltip: str) -> QPushButton:
    btn = QPushButton(f"{icon_text}\n{label}")
    btn.setToolTip(tooltip)
    btn.setCheckable(True)
    btn.setFixedWidth(72)
    btn.setMinimumHeight(56)
    btn.setCursor(Qt.PointingHandCursor)
    return btn


class MainWindow(QMainWindow):
    def __init__(self, app=None):
        super().__init__()
        self.app = app
        self.setWindowTitle("AI Assistant")
        self.setMinimumSize(860, 560)

        cfg = app.config if app else None
        w = cfg.get("ui.main_window.width", 960) if cfg else 960
        h = cfg.get("ui.main_window.height", 640) if cfg else 640
        self.resize(w, h)

        self._setup_ui()
        self._setup_status_bar()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # --- Sidebar ---
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(80)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(6, 12, 6, 12)
        sidebar_layout.setSpacing(4)

        # Logo
        title = QLabel("AI")
        title.setObjectName("sidebarTitle")
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title)

        sidebar_layout.addSpacing(8)

        # Nav buttons
        self._nav_group = QButtonGroup(self)
        self._nav_group.setExclusive(True)
        self._nav_buttons: list[QPushButton] = []

        for icon_text, label, tooltip in _NAV_ITEMS:
            btn = _make_nav_button(icon_text, label, tooltip)
            self._nav_group.addButton(btn)
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Sidebar version label
        ver = QLabel("v0.1")
        ver.setAlignment(Qt.AlignCenter)
        ver.setStyleSheet("color: #444460; font-size: 10px;")
        sidebar_layout.addWidget(ver)

        root_layout.addWidget(sidebar)

        # --- Content ---
        content_widget = QWidget()
        content_widget.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        content_layout.addWidget(self._stack)

        # Create panels
        self.chat_panel = ChatPanel(app=self.app)
        self.search_panel = SearchPanel(app=self.app)
        self.doc_panel = DocumentPanel(app=self.app)
        self.reader_panel = ChatReaderPanel(app=self.app)
        self.diary_panel = DiaryPanel(app=self.app)
        self.knowledge_panel = KnowledgePanel(app=self.app)
        self.settings_panel = SettingsPanel(app=self.app)

        self._panels = [
            self.chat_panel,
            self.search_panel,
            self.doc_panel,
            self.reader_panel,
            self.diary_panel,
            self.knowledge_panel,
            self.settings_panel,
        ]

        for panel in self._panels:
            self._stack.addWidget(panel)

        # Wire navigation
        for i, btn in enumerate(self._nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self._switch_page(idx))

        # Wire settings saved signal to refresh chat panel
        self.settings_panel.settings_saved.connect(self.chat_panel.load_models_from_config)

        root_layout.addWidget(content_widget, 1)

        # Default to chat page
        self._switch_page(0)

        # Initial load of models for chat panel
        self.chat_panel.load_models_from_config()

    def _switch_page(self, index: int) -> None:
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

    def _setup_status_bar(self) -> None:
        status = QStatusBar()
        self.setStatusBar(status)
        status.showMessage("就绪")

    def closeEvent(self, event) -> None:
        event.ignore()
        self.hide()
