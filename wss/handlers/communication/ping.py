"""
WebSocket ping/pong handlers.
"""

from datetime import datetime
from typing import Dict, Any

from wss.connection import WebSocketConnection


class PingHandler:
  """Handles ping/pong messages."""

  async def handle_ping(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle ping message"""
    await connection.send_message("pong", {
        "timestamp": datetime.utcnow().isoformat(),
        "connection_id": connection.connection_id
    })
