"""
WebSocket connection components.
"""

from .models import ConnectionState, AudioFormat
from .session import WebSocketConnection
from .manager import ConnectionManager

# Create global connection manager instance
connection_manager = ConnectionManager()

__all__ = [
    "ConnectionState",
    "AudioFormat",
    "WebSocketConnection",
    "ConnectionManager",
    "connection_manager"
]
