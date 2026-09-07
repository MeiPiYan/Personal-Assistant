from __future__ import annotations

import asyncio

from qasync import QEventLoop


def setup_async_loop(app) -> QEventLoop:
    """Create and set a qasync event loop for Qt + asyncio integration."""
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    return loop
