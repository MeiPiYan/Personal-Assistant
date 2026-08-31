from __future__ import annotations

import asyncio
from typing import Callable

from qasync import QEventLoop


def setup_async_loop(app) -> QEventLoop:
    """Create and set a qasync event loop for Qt + asyncio integration."""
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    return loop


async def run_in_executor(func: Callable, *args) -> any:
    """Run a blocking function in a thread executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, func, *args)
