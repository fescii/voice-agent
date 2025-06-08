"""
Audio processing for streaming.
"""
import base64
from typing import Optional

from core.logging.setup import get_logger
from ..models import AudioFrame, AudioHandler
from ..connection import ConnectionManager

logger = get_logger(__name__)


class AudioProcessor:
  """Handles audio data processing for streaming."""

  def __init__(self, connection_manager: ConnectionManager):
    self.connection_manager = connection_manager
    self.audio_handler: Optional[AudioHandler] = None

  def set_audio_handler(self, handler: AudioHandler):
    """
    Set the audio handler for processing incoming audio.

    Args:
        handler: Function to process incoming audio frames
    """
    self.audio_handler = handler
    logger.info("Audio handler set")

  async def send_audio(self, call_id: str, audio_data: bytes) -> bool:
    """
    Send audio data to Ringover.

    Args:
        call_id: ID of the call
        audio_data: Raw audio data to send

    Returns:
        True if sent successfully, False otherwise
    """
    if not self.connection_manager.is_connected():
      logger.warning("WebSocket not connected")
      return False

    message = {
        "type": "audio",
        "call_id": call_id,
        "data": audio_data.hex(),  # Convert bytes to hex string
        "format": "pcm",
        "sample_rate": 16000,
        "channels": 1
    }

    return await self.connection_manager.send_message(message)

  async def process_incoming_audio(self, call_id: str, data: dict):
    """
    Process incoming audio data from WebSocket.

    Args:
        call_id: ID of the call
        data: Audio data from WebSocket
    """
    try:
      # Extract audio data
      audio_hex = data.get("data", "")
      if not audio_hex:
        logger.warning("No audio data in message")
        return

      # Convert hex to bytes
      try:
        audio_bytes = bytes.fromhex(audio_hex)
      except ValueError:
        # Try base64 decoding as fallback
        try:
          audio_bytes = base64.b64decode(audio_hex)
        except Exception:
          logger.error("Failed to decode audio data")
          return

      # Create audio frame
      frame = AudioFrame(
          call_id=call_id,
          audio_data=audio_bytes,
          format=data.get("format", "pcm"),
          sample_rate=data.get("sample_rate", 16000),
          channels=data.get("channels", 1),
          timestamp=data.get("timestamp")
      )

      # Process with handler if available
      if self.audio_handler:
        try:
          response_audio = await self.audio_handler(frame)

          # Send response audio if provided
          if response_audio:
            await self.send_audio(call_id, response_audio)

        except Exception as e:
          logger.error(f"Audio handler failed: {e}")
      else:
        logger.debug(
            f"Received audio frame for call {call_id}, no handler set")

    except Exception as e:
      logger.error(f"Failed to process incoming audio: {e}")


class AudioControlManager:
  """Manages audio control operations like mute/unmute."""

  def __init__(self, connection_manager: ConnectionManager):
    self.connection_manager = connection_manager

  async def mute(self, call_id: str) -> bool:
    """
    Mute audio for the call.

    Args:
        call_id: ID of the call to mute

    Returns:
        True if mute successful
    """
    success = await self._send_control_message(call_id, "mute")
    if success:
      self.connection_manager.muted = True
      logger.info(f"Muted audio for call {call_id}")
    return success

  async def unmute(self, call_id: str) -> bool:
    """
    Unmute audio for the call.

    Args:
        call_id: ID of the call to unmute

    Returns:
        True if unmute successful
    """
    success = await self._send_control_message(call_id, "unmute")
    if success:
      self.connection_manager.muted = False
      logger.info(f"Unmuted audio for call {call_id}")
    return success

  async def _send_control_message(self, call_id: str, action: str, data: Optional[dict] = None) -> bool:
    """
    Send a control message to Ringover.

    Args:
        call_id: ID of the call
        action: Control action
        data: Additional control data

    Returns:
        True if sent successfully
    """
    if not self.connection_manager.is_connected():
      logger.warning("WebSocket not connected")
      return False

    message = {
        "type": "control",
        "call_id": call_id,
        "action": action,
        "data": data or {}
    }

    return await self.connection_manager.send_message(message)
