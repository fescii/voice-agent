"""
WebSocket audio control handlers.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from wss.connection import WebSocketConnection
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AudioControlHandler:
  """Handles audio control operations (mute/unmute)."""

  async def handle_mute(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle mute message"""
    try:
      if connection.call_context:
        metadata = getattr(connection, 'metadata', {})
        metadata["muted"] = True
        await connection.send_message("muted", {
            "call_id": connection.call_context.call_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Muted call for connection {connection.connection_id}")
    except Exception as e:
      logger.error(
          f"Error muting call for {connection.connection_id}: {str(e)}")

  async def handle_unmute(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle unmute message"""
    try:
      if connection.call_context:
        metadata = getattr(connection, 'metadata', {})
        metadata["muted"] = False
        await connection.send_message("unmuted", {
            "call_id": connection.call_context.call_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        logger.info(f"Unmuted call for connection {connection.connection_id}")
    except Exception as e:
      logger.error(
          f"Error unmuting call for {connection.connection_id}: {str(e)}")
