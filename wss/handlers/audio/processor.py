"""
WebSocket audio processing handlers.
"""

from services.stt.whisper import WhisperService
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AudioDataHandler:
  """Handles audio data processing."""

  def __init__(self, stt_service: WhisperService):
    """Initialize audio data handler."""
    self.stt_service = stt_service

  async def handle_audio_data(self, audio_data: bytes) -> None:
    """Handle incoming audio data"""
    try:
      # Process audio through STT service
      result = await self.stt_service.transcribe_audio(audio_data)
      text = result.get("text", "") if isinstance(result, dict) else ""
      if text and text.strip():
        logger.debug(f"Transcribed audio: {text[:50]}...")
        # Further processing would happen here

    except Exception as e:
      logger.error(f"Error processing audio data: {str(e)}")
