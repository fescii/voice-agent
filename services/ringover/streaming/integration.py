"""
Integration layer combining webhooks with official ringover-streamer.
"""
import asyncio
from typing import Dict, Any, Optional, TYPE_CHECKING

from core.logging.setup import get_logger
from .client import RingoverStreamerClient
from .manager import RingoverStreamerManager
from services.stt.whisper import WhisperService
from services.llm.orchestrator import LLMOrchestrator
from services.tts.elevenlabs import ElevenLabsService
from models.external.ringover.webhook import RingoverWebhookEvent

# Avoid circular import by using TYPE_CHECKING
if TYPE_CHECKING:
  from ..webhooks.orchestrator import RingoverWebhookOrchestrator

logger = get_logger(__name__)


class RingoverStreamerIntegration:
  """
  Integration layer that combines Ringover webhooks with the official ringover-streamer.

  This class implements the complete solution described in the documentation:
  1. Uses webhooks to receive call events (ringing, answered, ended)
  2. Connects to the official ringover-streamer for real-time audio
  3. Processes audio through STT/LLM/TTS pipeline
  4. Sends voicebot responses back through ringover-streamer
  """

  def __init__(self):
    """Initialize the integration."""
    self.streamer_manager = RingoverStreamerManager()
    self.streamer_client = RingoverStreamerClient()

    # AI services
    self.stt_service: Optional[WhisperService] = None
    self.llm_orchestrator: Optional[LLMOrchestrator] = None
    self.tts_service: Optional[ElevenLabsService] = None

    # Active call tracking
    self.active_calls: Dict[str, Dict[str, Any]] = {}

    # Note: webhook_orchestrator integration will be set up separately

  async def initialize(self):
    """Initialize all components."""
    try:
      logger.info("Initializing Ringover streamer integration...")

      # Initialize AI services
      await self._initialize_ai_services()

      # Ensure ringover-streamer is installed and start it
      if not await self.streamer_manager.start_streamer():
        raise Exception("Failed to start ringover-streamer service")

      # Give the streamer time to fully start
      await asyncio.sleep(3)

      logger.info("Ringover streamer integration initialized successfully")

    except Exception as e:
      logger.error(f"Failed to initialize Ringover integration: {e}")
      raise

  async def _initialize_ai_services(self):
    """Initialize AI services for voice processing."""
    try:
      # Initialize STT service
      from core.config.services.stt.whisper import WhisperConfig
      whisper_config = WhisperConfig()
      self.stt_service = WhisperService(whisper_config)

      # Initialize LLM orchestrator
      self.llm_orchestrator = LLMOrchestrator()

      # Initialize TTS service
      from core.config.services.tts.elevenlabs import ElevenLabsConfig
      elevenlabs_config = ElevenLabsConfig()
      self.tts_service = ElevenLabsService(elevenlabs_config)

      logger.info("AI services initialized successfully")

    except Exception as e:
      logger.error(f"Failed to initialize AI services: {e}")
      raise

  async def shutdown(self):
    """Shutdown all components."""
    try:
      logger.info("Shutting down Ringover integration...")

      # Disconnect from all active calls
      for call_id in list(self.active_calls.keys()):
        await self.disconnect_from_call(call_id)

      # Stop the ringover-streamer service
      await self.streamer_manager.stop_streamer()

      logger.info("Ringover integration shutdown complete")

    except Exception as e:
      logger.error(f"Error during shutdown: {e}")

  async def handle_webhook_event(self, event: RingoverWebhookEvent):
    """
    Handle webhook events and coordinate with ringover-streamer.

    Args:
        event: Webhook event from Ringover
    """
    try:
      event_type = event.event_type
      call_id = event.call_id

      if not call_id:
        logger.warning(f"Webhook event {event_type} has no call_id")
        return

      logger.info(f"Handling webhook event: {event_type} for call {call_id}")

      if event_type in ["call_ringing", "incoming_call"]:
        await self._handle_call_ringing(event)
      elif event_type in ["call_answered"]:
        await self._handle_call_answered(event)
      elif event_type in ["call_ended"]:
        await self._handle_call_ended(event)
      else:
        logger.debug(f"Unhandled webhook event type: {event_type}")

    except Exception as e:
      logger.error(f"Error handling webhook event: {e}")

  async def _handle_call_ringing(self, event: RingoverWebhookEvent):
    """Handle incoming call event."""
    call_id = event.call_id

    if not call_id:
      logger.warning("Call ringing event has no call_id")
      return

    # Track the call but don't connect to streamer yet
    self.active_calls[call_id] = {
        "status": "ringing",
        "event": event,
        "connected_to_streamer": False,
        "start_time": event.timestamp
    }

    logger.info(f"Call {call_id} is ringing")

  async def _handle_call_answered(self, event: RingoverWebhookEvent):
    """Handle call answered event - connect to ringover-streamer."""
    call_id = event.call_id

    if not call_id:
      logger.warning("Call answered event has no call_id")
      return

    if call_id not in self.active_calls:
      # Call wasn't tracked from ringing, create entry
      self.active_calls[call_id] = {
          "status": "answered",
          "event": event,
          "connected_to_streamer": False,
          "start_time": event.timestamp
      }
    else:
      self.active_calls[call_id]["status"] = "answered"

    # Connect to ringover-streamer for real-time audio
    success = await self.connect_to_call(call_id)
    if success:
      logger.info(
          f"Connected to ringover-streamer for answered call {call_id}")
    else:
      logger.error(
          f"Failed to connect to ringover-streamer for call {call_id}")

  async def _handle_call_ended(self, event: RingoverWebhookEvent):
    """Handle call ended event - disconnect from ringover-streamer."""
    call_id = event.call_id

    if call_id in self.active_calls:
      self.active_calls[call_id]["status"] = "ended"
      await self.disconnect_from_call(call_id)

    logger.info(f"Call {call_id} ended")

  async def connect_to_call(self, call_id: str) -> bool:
    """
    Connect to ringover-streamer for a specific call.

    Args:
        call_id: The call identifier

    Returns:
        True if connection successful
    """
    try:
      # Connect to the ringover-streamer
      success = await self.streamer_client.connect_to_streamer(call_id)
      if not success:
        return False

      # Update call tracking
      if call_id in self.active_calls:
        self.active_calls[call_id]["connected_to_streamer"] = True

      # Start listening for audio in background
      asyncio.create_task(self._listen_to_call_audio(call_id))

      return True

    except Exception as e:
      logger.error(f"Failed to connect to call {call_id}: {e}")
      return False

  async def disconnect_from_call(self, call_id: str):
    """
    Disconnect from ringover-streamer for a specific call.

    Args:
        call_id: The call identifier
    """
    try:
      await self.streamer_client.disconnect_from_streamer(call_id)

      if call_id in self.active_calls:
        del self.active_calls[call_id]

      logger.info(f"Disconnected from call {call_id}")

    except Exception as e:
      logger.error(f"Error disconnecting from call {call_id}: {e}")

  async def _listen_to_call_audio(self, call_id: str):
    """
    Listen to audio from ringover-streamer and process it.

    Args:
        call_id: The call identifier
    """
    try:
      await self.streamer_client.listen_for_audio(
          call_id,
          self._process_incoming_audio
      )
    except Exception as e:
      logger.error(f"Error listening to call audio for {call_id}: {e}")

  async def _process_incoming_audio(self, call_id: str, audio_data: bytes):
    """
    Process incoming audio through STT/LLM/TTS pipeline.

    Args:
        call_id: The call identifier
        audio_data: Raw audio bytes from Ringover
    """
    try:
      if not self.stt_service or not self.llm_orchestrator or not self.tts_service:
        logger.warning(
            "AI services not initialized, skipping audio processing")
        return

      # Convert audio to text using STT
      transcript_result = await self.stt_service.transcribe_audio(audio_data)

      # Extract text from result (STT service might return dict or string)
      if isinstance(transcript_result, dict):
        transcript = transcript_result.get("text", "")
      else:
        transcript = str(transcript_result) if transcript_result else ""

      if not transcript or not transcript.strip():
        return  # No speech detected

      logger.info(f"Call {call_id} - Transcribed: {transcript}")

      # Get LLM response
      messages = [{"role": "user", "content": transcript}]
      llm_response = await self.llm_orchestrator.generate_response(
          messages,
          context={"call_id": call_id}
      )

      if not llm_response or not llm_response.get_content():
        return

      response_text = llm_response.get_content()
      logger.info(f"Call {call_id} - LLM Response: {response_text}")

      # Convert response to audio using TTS
      audio_response = await self.tts_service.synthesize_speech(response_text)
      if audio_response:
        # Stream the response back to the caller
        await self.streamer_client.stream_audio_data(
            call_id,
            audio_response,
            audio_format="raw",
            sample_rate=16000
        )

    except Exception as e:
      logger.error(f"Error processing audio for call {call_id}: {e}")

  async def start(self):
    """Start the integration after initialization."""
    try:
      logger.info("Starting Ringover streamer integration...")

      # Connect the streamer client
      await self.streamer_client.connect()

      logger.info("Ringover streamer integration started successfully")

    except Exception as e:
      logger.error(f"Failed to start Ringover integration: {e}")
      raise

  async def stop(self):
    """Stop the integration."""
    try:
      logger.info("Stopping Ringover streamer integration...")

      # Shutdown components
      await self.shutdown()

      logger.info("Ringover streamer integration stopped successfully")

    except Exception as e:
      logger.error(f"Failed to stop Ringover integration: {e}")
      raise

  def get_active_calls(self) -> Dict[str, Dict[str, Any]]:
    """Get currently active calls."""
    return self.active_calls.copy()

  def get_integration_status(self) -> Dict[str, Any]:
    """Get the status of the integration."""
    streamer_status = self.streamer_manager.get_status()

    return {
        "streamer_manager": streamer_status,
        "streamer_client_connected": self.streamer_client.is_connected,
        "active_calls": len(self.active_calls),
        "ai_services": {
            "stt_initialized": self.stt_service is not None,
            "llm_initialized": self.llm_orchestrator is not None,
            "tts_initialized": self.tts_service is not None
        }
    }

  def get_streamer_status(self) -> str:
    """Get the status of the streamer manager."""
    status = self.streamer_manager.get_status()
    return status.get("status", "unknown")
