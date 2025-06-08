"""
Call coordination and service initialization.
"""

from typing import Optional
from core.logging.setup import get_logger
from core.config.registry import config_registry
from services.ringover import RingoverAPIClient
from services.llm.orchestrator import LLMOrchestrator
from services.audio.processor import AudioProcessor
from services.transcription.realtime import RealtimeTranscription
from services.transcription.processor import TranscriptionProcessor
from services.tts.elevenlabs import ElevenLabsService

logger = get_logger(__name__)


class CallCoordinationManager:
  """Manages coordination between call services and components."""

  def __init__(self):
    """Initialize call coordination manager."""
    self._initialize_services()

  def _initialize_services(self):
    """Initialize all required services using centralized config."""
    # Initialize Ringover client
    self.ringover_client = RingoverAPIClient()

    # Component managers
    self.llm_orchestrator = LLMOrchestrator()
    self.audio_processor = AudioProcessor()

    # Initialize transcription service
    self._initialize_transcription_service()

    # Initialize TTS service
    self._initialize_tts_service()

  def _initialize_transcription_service(self):
    """Initialize speech-to-text transcription service."""
    try:
      from core.config.services.stt.whisper import WhisperConfig

      stt_config = config_registry.stt
      whisper_config = WhisperConfig(
          api_key=stt_config.api_key,
          model=stt_config.model
      )
      transcription_processor = TranscriptionProcessor(whisper_config)
      self.transcription_service = RealtimeTranscription(
          transcription_processor)
      logger.info("Transcription service initialized successfully")
    except Exception as e:
      logger.error(f"Failed to initialize transcription service: {str(e)}")
      self.transcription_service = None

  def _initialize_tts_service(self):
    """Initialize text-to-speech service."""
    try:
      tts_config = config_registry.tts
      if tts_config.api_key:
        from core.config.services.tts.elevenlabs import ElevenLabsConfig
        elevenlabs_config = ElevenLabsConfig(
            api_key=tts_config.api_key,
            voice_id=tts_config.voice_id
        )
        self.tts_service = ElevenLabsService(elevenlabs_config)
        logger.info("TTS service initialized successfully")
      else:
        self.tts_service = None
        logger.warning("TTS service not initialized - no API key provided")
    except Exception as e:
      logger.error(f"Failed to initialize TTS service: {str(e)}")
      self.tts_service = None

  async def get_services(self):
    """Get all initialized services."""
    return {
        'ringover_client': self.ringover_client,
        'llm_orchestrator': self.llm_orchestrator,
        'audio_processor': self.audio_processor,
        'transcription_service': self.transcription_service,
        'tts_service': self.tts_service
    }
