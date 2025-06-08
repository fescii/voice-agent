"""
Message handler for processing different types of WebSocket messages.
"""
from typing import Dict, Any

from core.logging.setup import get_logger
from ..models import AudioFrame

logger = get_logger(__name__)


class MessageHandler:
  """Base handler for WebSocket messages."""

  def __init__(self, connection_manager, audio_processor):
    """
    Initialize message handler.

    Args:
        connection_manager: Connection manager instance
        audio_processor: Audio processor instance
    """
    self.connection_manager = connection_manager
    self.audio_processor = audio_processor

  async def handle_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming WebSocket message.

    Args:
        call_id: ID of the call
        data: Message data
    """
    message_type = data.get("type")

    if message_type == "audio":
      await self.handle_audio_message(call_id, data)
    elif message_type == "event":
      await self.handle_event_message(call_id, data)
    elif message_type == "control":
      await self.handle_control_message(call_id, data)
    else:
      logger.warning(f"Unknown message type: {message_type}")

  async def handle_audio_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming audio message.

    Args:
        call_id: ID of the call
        data: Audio message data
    """
    if not self.audio_processor.audio_handler:
      return

    try:
      # Convert hex string back to bytes
      audio_data = bytes.fromhex(data.get("data", ""))

      audio_frame = AudioFrame(
          call_id=call_id,
          audio_data=audio_data,
          format=data.get("format", "pcm"),
          sample_rate=data.get("sample_rate", 16000),
          channels=data.get("channels", 1),
          timestamp=data.get("timestamp")
      )

      # Process audio and get response
      response_audio = await self.audio_processor.audio_handler(audio_frame)

      # Send response audio back if available
      if response_audio:
        await self.audio_processor.send_audio(call_id, response_audio)

    except Exception as e:
      logger.error(f"Error handling audio message: {e}")

  async def handle_event_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming event message.

    Args:
        call_id: ID of the call
        data: Event message data
    """
    # This will be handled by the message router when event handler is set
    pass

  async def handle_control_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming control message.

    Args:
        call_id: ID of the call
        data: Control message data
    """
    action = data.get("action")
    logger.info(f"Received control message for call {call_id}: {action}")

    # Handle specific control actions
    if action == "end_stream":
      await self.connection_manager.disconnect(call_id)
