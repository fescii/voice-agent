"""
STT (Speech-to-Text) startup service.
"""
from typing import Dict, Any, TYPE_CHECKING

from .base import BaseStartupService
from services.stt import WhisperService
from core.config.services.stt.whisper import WhisperConfig
from core.config.registry import config_registry
from core.logging.setup import get_logger

if TYPE_CHECKING:
  from core.startup.manager import StartupContext

logger = get_logger(__name__)


class STTService(BaseStartupService):
  """Speech-to-Text service initialization."""

  def __init__(self):
    super().__init__("stt", is_critical=True)
    self._stt_service = None

  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """Initialize STT service."""
    try:
      # Get STT configuration
      stt_config = config_registry.stt

      # Create WhisperConfig from STTConfig
      whisper_config = WhisperConfig(
          api_key=stt_config.api_key,
          model=stt_config.model or "whisper-1",
          language=stt_config.language.split(
              # Convert "en-US" to "en"
              '-')[0] if stt_config.language else "en"
      )

      # Initialize Whisper STT service
      self._stt_service = WhisperService(whisper_config)

      # Test STT service (optional)
      # For now just verify configuration is accessible

      logger.info("STT service (Whisper) initialized successfully")

      return {
          "provider": "whisper",
          "model": whisper_config.model,
          "language": whisper_config.language,
          "sample_rate": stt_config.sample_rate,
          "status": "initialized",
          "service": self._stt_service
      }

    except Exception as e:
      logger.error(f"STT service initialization failed: {e}")
      raise  # Critical service, should fail startup

  async def cleanup(self, context: "StartupContext") -> None:
    """Cleanup STT resources."""
    try:
      if self._stt_service:
        # Cleanup any STT resources if needed
        pass
      logger.info("STT service cleaned up")
    except Exception as e:
      logger.error(f"Error cleaning up STT service: {e}")

  def get_health_check(self) -> Dict[str, Any]:
    """Get STT service health information."""
    if self._stt_service:
      return {
          "service": self.name,
          "status": "healthy",
          "critical": self.is_critical,
          "provider": "whisper"
      }
    else:
      return {
          "service": self.name,
          "status": "not_initialized",
          "critical": self.is_critical
      }
