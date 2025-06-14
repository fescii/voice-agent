"""
Ringover streaming service initialization.
"""
from typing import Dict, Any, Optional, List, TYPE_CHECKING, TypeVar

from core.logging.setup import get_logger
from core.config.registry import config_registry
from core.config.services.stt.whisper import WhisperConfig
# Import locally to avoid circular imports
from services.stt.whisper import WhisperService
from services.llm.prompt.builder import PromptBuilder

if TYPE_CHECKING:
  from .handler import RingoverStreamHandler

# Type alias for StreamHandler to avoid circular imports
TStreamHandler = TypeVar('TStreamHandler')

logger = get_logger(__name__)


class RingoverStreamingService:
  """
  Main service for managing Ringover audio streaming.

  This service creates and manages stream handlers for each active call,
  coordinating audio processing, transcription, and response pipelines.
  """

  def __init__(self):
    """Initialize the Ringover streaming service."""
    self.active_streams: Dict[str, Any] = {}

    # Get STT config from centralized registry
    stt_config = config_registry.stt
    from services.llm.prompt.manager import PromptManager

    # Initialize services
    whisper_config = self._convert_to_whisper_config(stt_config)
    self.transcription_service = WhisperService(whisper_config)
    self.prompt_builder = PromptBuilder(PromptManager())

  def _convert_to_whisper_config(self, stt_config) -> WhisperConfig:
    """Convert generic STT config to Whisper-specific config."""
    return WhisperConfig(
        api_key=stt_config.api_key,
        model=stt_config.model or "whisper-1",
        language=stt_config.language.split(
            "-")[0] if stt_config.language else "en",  # Convert en-US to en
        response_format="json",
        temperature=0.0
    )

  async def create_stream_handler(self, call_id: str) -> Any:
    """
    Create a new stream handler for a call.

    Args:
        call_id: The unique ID of the call

    Returns:
        A configured stream handler instance
    """
    if call_id in self.active_streams:
      # Return existing stream handler if already created
      return self.active_streams[call_id]

    # Create a new handler
    from .handler import RingoverStreamHandler

    handler = RingoverStreamHandler(
        transcriber=self.transcription_service,
        prompt_builder=self.prompt_builder
    )

    # Store in active streams
    self.active_streams[call_id] = handler
    logger.info(f"Created stream handler for call {call_id}")

    return handler

  async def close_stream(self, call_id: str) -> None:
    """
    Close and remove a stream handler.

    Args:
        call_id: The unique ID of the call to close
    """
    if call_id in self.active_streams:
      # Clean up the handler (if needed)
      handler = self.active_streams[call_id]
      del self.active_streams[call_id]
      logger.info(f"Closed stream handler for call {call_id}")

  def get_active_streams(self) -> List[str]:
    """
    Get a list of active stream call IDs.

    Returns:
        List of active call IDs
    """
    return list(self.active_streams.keys())

  def get_stream_handler(self, call_id: str) -> Optional[Any]:
    """
    Get an existing stream handler by call ID.

    Args:
        call_id: The unique ID of the call

    Returns:
        The stream handler instance or None if not found
    """
    return self.active_streams.get(call_id)
