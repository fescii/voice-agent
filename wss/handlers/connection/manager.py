"""
WebSocket connection lifecycle handlers.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from wss.connection import WebSocketConnection
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ConnectionManager:
  """Manages WebSocket connection lifecycle."""

  def __init__(self, message_handlers: Dict[str, Any], audio_handler, disconnect_handler):
    """Initialize connection manager."""
    self.message_handlers = message_handlers
    self.audio_handler = audio_handler
    self.disconnect_handler = disconnect_handler

  async def handle_connection(self, connection: WebSocketConnection) -> None:
    """Handle a new WebSocket connection"""
    try:
      logger.info(
          f"Handling new WebSocket connection: {connection.connection_id}")

      # Set up message handlers
      for message_type, handler in self.message_handlers.items():
        connection.add_message_handler(message_type, handler)

      # Set up audio handler
      connection.add_audio_handler(self.audio_handler)

      # Set up disconnect handler
      connection.add_disconnect_handler(self.disconnect_handler)

      # Send welcome message
      await connection.send_message("welcome", {
          "connection_id": connection.connection_id,
          "server_time": datetime.utcnow().isoformat(),
          "supported_audio_formats": ["pcm_16000", "mulaw_8000", "opus"],
          "protocol_version": "1.0"
      })

      # Start message loop
      await self._message_loop(connection)

    except Exception as e:
      logger.error(
          f"Error handling connection {connection.connection_id}: {str(e)}")
      await connection.close(code=1011, reason="Internal server error")

  async def _message_loop(self, connection: WebSocketConnection) -> None:
    """Main message processing loop for a connection"""
    try:
      while connection.is_active():
        message = await connection.receive_message()
        if message is None:
          break

        await self._process_message(connection, message)

    except Exception as e:
      logger.error(
          f"Message loop error for {connection.connection_id}: {str(e)}")
    finally:
      logger.info(f"Message loop ended for {connection.connection_id}")

  async def _process_message(self, connection: WebSocketConnection, message: Dict[str, Any]) -> None:
    """Process a single message"""
    try:
      message_type = message.get("type")
      if not message_type:
        await connection.send_message("error", {
            "message": "Message type is required",
            "code": "INVALID_MESSAGE"
        })
        return

      handler = connection.message_handlers.get(message_type)
      if not handler:
        await connection.send_message("error", {
            "message": f"Unknown message type: {message_type}",
            "code": "UNKNOWN_MESSAGE_TYPE"
        })
        return

      # Call the handler
      await handler(connection, message.get("data", {}))

    except Exception as e:
      logger.error(
          f"Error processing message {message.get('type')} for {connection.connection_id}: {str(e)}")
      await connection.send_message("error", {
          "message": "Failed to process message",
          "code": "PROCESSING_ERROR"
      })
