"""
WebSocket services initialization.
"""

from services.audio.streaming import AudioStreamService
from services.call.management.supervisor import CallSupervisor
from core.config.registry import config_registry
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ServiceInitializer:
  """Initializes all services needed for WebSocket handlers."""

  def __init__(self):
    self.audio_stream_service = None
    self.call_supervisor = None
    self.stt_service = None
    self.tts_service = None

  def initialize(self):
    """Initialize all services."""
    # Initialize core services
    self.audio_stream_service = AudioStreamService()
    self.call_supervisor = CallSupervisor()

    # TODO: Initialize STT and TTS services with centralized config
    # self.stt_service = WhisperService(config_registry.stt)
    # self.tts_service = ElevenLabsService(config_registry.tts)
    self.stt_service = None  # Placeholder
    self.tts_service = None  # Placeholder

    logger.info("WebSocket services initialized")

  def get_services(self):
    """Get initialized services."""
    return {
        'audio_stream': self.audio_stream_service,
        'call_supervisor': self.call_supervisor,
        'stt': self.stt_service,
        'tts': self.tts_service
    }
