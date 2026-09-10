"""Offscreen UI layout consistency tests.

Verifies that boxes (containers) and the fields inside them have matching
sizes: unified control heights, no clipped button text, and a sidebar that
fits its navigation buttons.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

from PySide6.QtWidgets import (
    QApplication, QLineEdit, QComboBox, QPushButton, QSpinBox, QFrame,
)

from src.ui.styles import ThemeManager


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


# Two-char CJK buttons used across panels with their fixed widths.
TWO_CHAR_BUTTONS = [
    ("清空", 64), ("本地", 64), ("相关", 64), ("筛选", 64),
    ("刷新", 64), ("搜索", 64), ("添加", 64), ("提取", 64),
]

# Allowed height difference between controls placed in the same row.
CONTROL_HEIGHT_TOLERANCE = 4


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_control_heights_match(theme, qapp):
    """Line edits, combos, spin boxes and buttons must be the same height."""
    ThemeManager.apply(theme)

    line = QLineEdit()
    combo = QComboBox()
    combo.addItems(["选项一"])
    spin = QSpinBox()
    spin.setRange(1, 720)
    spin.setSuffix(" h")
    btn = QPushButton("保存")
    btn_secondary = QPushButton("本地")
    btn_secondary.setObjectName("secondaryBtn")

    heights = {
        "QLineEdit": line.sizeHint().height(),
        "QComboBox": combo.sizeHint().height(),
        "QSpinBox": spin.sizeHint().height(),
        "QPushButton": btn.sizeHint().height(),
        "secondaryBtn": btn_secondary.sizeHint().height(),
    }
    spread = max(heights.values()) - min(heights.values())
    assert spread <= CONTROL_HEIGHT_TOLERANCE, heights


@pytest.mark.parametrize("theme", ["dark", "light"])
@pytest.mark.parametrize("text,width", TWO_CHAR_BUTTONS)
def test_two_char_buttons_fit_fixed_width(theme, qapp, text, width):
    """Fixed-width buttons must be wide enough to show two CJK characters."""
    ThemeManager.apply(theme)
    btn = QPushButton(text)
    btn.setFixedWidth(width)
    assert btn.sizeHint().width() <= width, (
        f"按钮 '{text}' 需要 {btn.sizeHint().width()}px，超过固定宽度 {width}px（文字会被截断）"
    )


def test_sidebar_fits_nav_buttons(qapp):
    """The 80px sidebar must fully contain its 72px navigation buttons."""
    from src.ui.main_window import MainWindow

    ThemeManager.apply("dark")
    win = MainWindow(app=None)
    win.show()
    QApplication.processEvents()

    sidebar = win.findChild(QFrame, "sidebar")
    assert sidebar is not None
    margins = sidebar.layout().contentsMargins()
    available = sidebar.width() - margins.left() - margins.right()
    for btn in win._nav_buttons:
        assert btn.width() <= available, (
            f"导航按钮宽 {btn.width()}px，侧栏可用空间仅 {available}px"
        )
    win.close()


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_panels_instantiate(theme, qapp):
    """All panels must build without errors under both themes."""
    from src.ui.chat_panel import ChatPanel
    from src.ui.chat_reader_panel import ChatReaderPanel
    from src.ui.diary_panel import DiaryPanel
    from src.ui.document_panel import DocumentPanel
    from src.ui.knowledge_panel import KnowledgePanel
    from src.ui.search_panel import SearchPanel
    from src.ui.settings_panel import SettingsPanel

    ThemeManager.apply(theme)
    panels = [
        ChatPanel(app=None),
        SearchPanel(app=None),
        DocumentPanel(app=None),
        ChatReaderPanel(app=None),
        DiaryPanel(app=None),
        KnowledgePanel(app=None),
        SettingsPanel(app=None),
    ]
    for panel in panels:
        assert panel is not None
        panel.deleteLater()
    QApplication.processEvents()
