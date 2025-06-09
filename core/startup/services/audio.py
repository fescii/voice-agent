"""
Audio service startup initialization.
Handles audio processing and streaming services.
"""
import os
from typing import Dict, Any

from .base import BaseStartupService
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AudioService(BaseStartupService):
  """Audio processing service startup handler."""

  def __init__(self):
    super().__init__("audio", is_critical=True)

  async def initialize(self, context) -> Dict[str, Any]:
    """Initialize audio processing services."""
    try:
      # Initialize audio processor
      from services.audio.processor import AudioProcessor

      # Get audio configuration from environment or use defaults
      audio_config = {
          "sample_rate": int(os.getenv("STT_SAMPLE_RATE", "16000")),
          "chunk_size": int(os.getenv("AUDIO_CHUNK_SIZE", "1024")),
      }

      # Initialize processor
      processor = AudioProcessor()

      logger.info("Audio processor initialized successfully")

      return {
          "processor": processor,
          "sample_rate": audio_config.get("sample_rate", 16000),
          "chunk_size": audio_config.get("chunk_size", 1024),
          "status": "ready"
      }

    except Exception as e:
      logger.error(f"Failed to initialize audio service: {e}")
      raise

  async def cleanup(self, context) -> None:
    """Cleanup audio services."""
    try:
      logger.info("Cleaning up audio service...")
      # Audio services typically don't need explicit cleanup
      # as they're stateless processors

    except Exception as e:
      logger.error(f"Error cleaning up audio service: {e}")
