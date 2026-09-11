"""Personal AI Assistant - Windows Desktop Application."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.app.application import Application
from src.ui.main_window import MainWindow
from src.ui.floating_ball import FloatingBall
from src.ui.styles import ThemeManager
from src.ai.engine import AIEngine
from src.storage.database import Database
from src.storage.dao import DAO
from src.storage.backup import BackupManager
from src.utils.async_bridge import setup_async_loop


def _resolve_project_path(p: str | Path) -> Path:
    """Resolve a config path against the project root when it is relative."""
    path = Path(p)
    if not path.is_absolute():
        path = Path(__file__).resolve().parent / path
    return path


async def init_db(app: Application) -> None:
    db = Database()
    db_path = app.config.get("storage.db_path", "data/assistant.db")
    await db.connect(str(_resolve_project_path(db_path)))


async def init_backup(app: Application) -> BackupManager:
    """Initialize backup manager and run startup backup if configured."""
    backup_mgr = BackupManager()

    # Read backup config
    backup_cfg = app.config.get("backup", {})
    db_path = app.config.get("storage.db_path", "data/assistant.db")

    backup_mgr.configure(
        backup_dir=_resolve_project_path(backup_cfg.get("directory", "data/backups")),
        db_path=_resolve_project_path(db_path),
        config_path=str(Path(__file__).parent / "config" / "settings.yaml"),
        max_backups=backup_cfg.get("max_backups", 10),
        interval_hours=backup_cfg.get("interval_hours", 24),
        auto_on_startup=backup_cfg.get("auto_on_startup", True),
        enabled=backup_cfg.get("enabled", True),
    )

    # Auto-backup on startup
    if backup_cfg.get("enabled", True) and backup_cfg.get("auto_on_startup", True):
        try:
            await backup_mgr.backup_all()
            await backup_mgr.cleanup_old_backups()
        except Exception:
            pass  # Startup backup failure should not block app launch

    # Start periodic backup
    if backup_cfg.get("enabled", True) and backup_cfg.get("interval_hours", 24) > 0:
        await backup_mgr.start_auto_backup()

    return backup_mgr


def main() -> None:
    app = Application()

    # Theme – load saved preference from config
    ThemeManager.load_from_config(app.config)

    # Main window
    main_window = MainWindow(app=app)
    app.set_main_window(main_window)

    # Floating ball
    ball_cfg = app.config.get("ui.floating_ball", {})
    ball = FloatingBall(
        size=ball_cfg.get("size", 48),
        opacity=ball_cfg.get("opacity", 0.85),
    )
    app.set_floating_ball(ball)

    # Wire up signals
    def show_main():
        main_window.show()
        main_window.activateWindow()
        main_window.raise_()
        ball.hide()

    app.signals.show_main_window.connect(show_main)
    ball.clicked.connect(show_main)

    def close_override(event):
        event.ignore()
        main_window.hide()
        ball.show()

    main_window.closeEvent = close_override

    # AI Engine
    ai_engine = AIEngine(config=app.config)
    main_window.chat_panel.set_ai_engine(ai_engine)
    main_window.search_panel.set_ai_engine(ai_engine)
    main_window.doc_panel.set_ai_engine(ai_engine)
    main_window.diary_panel.set_ai_engine(ai_engine)

    # Show main window + floating ball
    main_window.show()
    ball.show()

    # Setup async loop (qasync integrates Qt + asyncio)
    loop = setup_async_loop(app.app)

    async def startup():
        await init_db(app)
        # Create DAO after DB is connected and pass to panels
        dao = DAO()
        main_window.set_dao(dao)
        # Initialize backup manager
        backup_mgr = await init_backup(app)
        main_window.set_backup_manager(backup_mgr)

    loop.create_task(startup())

    # Setup system tray
    app.setup_tray()

    with loop:
        loop.run_forever()

    sys.exit(0)


if __name__ == "__main__":
    main()
