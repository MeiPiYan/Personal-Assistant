"""Personal AI Assistant - Windows Desktop Application."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.app.application import Application
from src.app.config import Config
from src.ui.main_window import MainWindow
from src.ui.floating_ball import FloatingBall
from src.ui.styles import ThemeManager
from src.ai.engine import AIEngine
from src.storage.database import Database
from src.utils.async_bridge import setup_async_loop


async def init_db(app: Application) -> None:
    db = Database()
    db_path = app.config.get("storage.db_path", "data/assistant.db")
    await db.connect(db_path)


def main() -> None:
    app = Application()

    # Theme
    theme = app.config.get("ui.theme", "dark")
    ThemeManager.apply(theme)

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

    def hide_main():
        main_window.hide()
        ball.show()

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

    # Show floating ball
    ball.show()

    # Setup async loop and run
    loop = setup_async_loop(app.app)

    async def startup():
        await init_db(app)

    loop.create_task(startup())

    exit_code = app.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
