"""
TTS (Text-to-Speech) startup service.
"""
from typing import Dict, Any, TYPE_CHECKING

from .base import BaseStartupService
from services.tts import ElevenLabsService
from core.config.services.tts.elevenlabs import ElevenLabsConfig
from core.config.registry import config_registry
from core.logging.setup import get_logger

if TYPE_CHECKING:
  from core.startup.manager import StartupContext

logger = get_logger(__name__)


class TTSService(BaseStartupService):
  """Text-to-Speech service initialization."""

  def __init__(self):
    super().__init__("tts", is_critical=True)
    self._tts_service = None

  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """Initialize TTS service."""
    try:
      # Get TTS configuration
      tts_config = config_registry.tts

      # Create ElevenLabsConfig from TTSConfig
      elevenlabs_config = ElevenLabsConfig(
          api_key=tts_config.api_key,
          voice_id=tts_config.voice_id,
          model_id=tts_config.model or "eleven_monolingual_v1"
      )

      # Initialize ElevenLabs TTS service
      self._tts_service = ElevenLabsService(elevenlabs_config)

      # Test TTS service (optional)
      # For now just verify configuration is accessible

      logger.info("TTS service (ElevenLabs) initialized successfully")

      return {
          "provider": "elevenlabs",
          "model": elevenlabs_config.model_id,
          "voice_id": elevenlabs_config.voice_id,
          "status": "initialized",
          "service": self._tts_service
      }

    except Exception as e:
      logger.error(f"TTS service initialization failed: {e}")
      raise  # Critical service, should fail startup

  async def cleanup(self, context: "StartupContext") -> None:
    """Cleanup TTS resources."""
    try:
      if self._tts_service:
        # Cleanup any TTS resources if needed
        pass
      logger.info("TTS service cleaned up")
    except Exception as e:
      logger.error(f"Error cleaning up TTS service: {e}")

  def get_health_check(self) -> Dict[str, Any]:
    """Get TTS service health information."""
    if self._tts_service:
      return {
          "service": self.name,
          "status": "healthy",
          "critical": self.is_critical,
          "provider": "elevenlabs"
      }
    else:
      return {
          "service": self.name,
          "status": "not_initialized",
          "critical": self.is_critical
      }
