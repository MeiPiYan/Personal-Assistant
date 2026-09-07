from __future__ import annotations

from PySide6.QtCore import Signal, QObject
from ..storage.models import ChatMessage


class ChatReaderBase(QObject):
    """Abstract base for chat message readers."""
    message_received = Signal(object)  # ChatMessage
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running
