"""
WebSocket disconnect handlers.
"""

from wss.connection import WebSocketConnection
from services.call.management.supervisor import CallSupervisor
from core.logging.setup import get_logger

logger = get_logger(__name__)


class DisconnectHandler:
  """Handles WebSocket connection disconnects."""

  def __init__(self, call_supervisor: CallSupervisor):
    """Initialize disconnect handler."""
    self.call_supervisor = call_supervisor

  async def handle_disconnect(self, connection: WebSocketConnection) -> None:
    """Handle connection disconnect"""
    try:
      logger.info(f"Handling disconnect for {connection.connection_id}")

      # End any active call
      if connection.call_context:
        await self.call_supervisor.end_call(connection.call_context.call_id)

      # Clean up resources
      await self._cleanup_connection_resources(connection)

    except Exception as e:
      logger.error(
          f"Error handling disconnect for {connection.connection_id}: {str(e)}")

  async def _cleanup_connection_resources(self, connection: WebSocketConnection) -> None:
    """Clean up resources associated with a connection"""
    try:
      # Stop any audio streaming
      audio_stream = getattr(connection, 'audio_stream', None)
      if audio_stream and hasattr(audio_stream, 'stop'):
        await audio_stream.stop()

      # Clear any cached data
      metadata = getattr(connection, 'metadata', None)
      if metadata and hasattr(metadata, 'clear'):
        metadata.clear()

      logger.debug(f"Cleaned up resources for {connection.connection_id}")

    except Exception as e:
      logger.error(
          f"Error cleaning up resources for {connection.connection_id}: {str(e)}")
