from __future__ import annotations

from PySide6.QtCore import Signal, QObject
from .models import ChatMessage


class MessageProcessor(QObject):
    """Message queue, deduplication, and batch dispatch."""
    batch_ready = Signal(list)  # list of ChatMessage

    def __init__(self, batch_size: int = 20, batch_interval: int = 300, parent=None):
        super().__init__(parent)
        self._batch_size = batch_size
        self._batch_interval = batch_interval
        self._buffer: list[ChatMessage] = []
        self._seen_ids: set[str] = set()

    def add_message(self, msg: ChatMessage) -> None:
        msg_id = f"{msg.platform}:{msg.sender}:{msg.content[:50]}:{msg.created_at}"
        if msg_id in self._seen_ids:
            return
        self._seen_ids.add(msg_id)
        self._buffer.append(msg)

        if len(self._buffer) >= self._batch_size:
            self._flush()

    def _flush(self) -> None:
        if self._buffer:
            self.batch_ready.emit(list(self._buffer))
            self._buffer.clear()

    def force_flush(self) -> None:
        self._flush()
