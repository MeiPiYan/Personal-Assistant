"""UI async task tracking (U-P0).

Keeps strong references to fire-and-forget tasks so they cannot be garbage
collected while pending (CPython would warn "Task was destroyed but it is
pending"). Tasks remove themselves on completion.
"""

from __future__ import annotations

import asyncio

_tasks: set[asyncio.Task] = set()


def spawn_ui(coro) -> asyncio.Task:
    """Like ``asyncio.ensure_future`` but tracked against GC."""
    task = asyncio.ensure_future(coro)
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    return task


def pending_tasks() -> tuple[asyncio.Task, ...]:
    """Snapshot of currently tracked (possibly running) tasks."""
    return tuple(t for t in _tasks if not t.done())
