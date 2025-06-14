"""
Streaming manager for handling audio stream setup and coordination.
Manages connections to ringover-streamer and audio processing.
"""
import asyncio
import json
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from services.ringover.streaming.service import RingoverStreamingService
from services.ringover.streaming.client import RingoverStreamerClient
from ..audio.processor import AudioProcessor

logger = get_logger(__name__)


class StreamingManager:
  """
  Manages streaming connections and audio processing setup.
  Coordinates between Ringover streaming service and external streamer client.
  """

  def __init__(self, startup_context: Any = None):
    """
    Initialize the streaming manager.

    Args:
        startup_context: Application startup context for service access
    """
    self.streaming_service = RingoverStreamingService()
    self.streamer_client = RingoverStreamerClient()
    self.active_streams: Dict[str, Dict[str, Any]] = {}

    # Initialize audio processor with startup context
    self.audio_processor = None
    if startup_context:
      self.audio_processor = AudioProcessor(startup_context)
      logger.info("Streaming manager initialized with audio processor")
    else:
      logger.warning(
          "Streaming manager initialized without startup context - audio processing disabled")

    logger.info("Streaming manager initialized")

  async def initialize_streaming(self, call_id: str, session_id: str, agent_id: str) -> bool:
    """
    Initialize streaming for a call.

    Args:
        call_id: Ringover call ID
        session_id: Internal session ID
        agent_id: Agent handling the call

    Returns:
        True if streaming initialized successfully
    """
    try:
      logger.info(f"🔌 Initializing streaming for call {call_id}")

      # Add a small delay to ensure the call is fully established
      await asyncio.sleep(2)

      # Create stream handler for this call
      stream_handler = await self.streaming_service.create_stream_handler(call_id)

      if stream_handler:
        logger.info(f"✅ Stream handler created for call {call_id}")
      else:
        logger.warning(
            f"⚠️  Stream handler creation not fully implemented for call {call_id}")

      # Track the streaming session
      self.active_streams[call_id] = {
          "session_id": session_id,
          "agent_id": agent_id,
          "stream_handler": stream_handler,
          "streamer_connected": False,
          "streaming_enabled": True
      }

      logger.info(f"✅ Streaming initialized for call {call_id}")
      return True

    except Exception as e:
      logger.error(
          f"Failed to initialize streaming for call {call_id}: {str(e)}")
      return False

  async def connect_to_streamer(self, call_id: str) -> bool:
    """
    Connect to the external ringover-streamer for a specific call.

    Args:
        call_id: Ringover call ID

    Returns:
        True if connection successful
    """
    try:
      logger.info(f"🔌 Connecting to ringover-streamer for call {call_id}")

      # Connect to the external ringover-streamer
      connected = await self.streamer_client.connect_to_streamer(call_id)

      if connected and call_id in self.active_streams:
        self.active_streams[call_id]["streamer_connected"] = True
        logger.info(f"✅ Connected to ringover-streamer for call {call_id}")
        return True
      else:
        logger.error(
            f"❌ Failed to connect to ringover-streamer for call {call_id}")
        return False

    except Exception as e:
      logger.error(
          f"Error connecting to ringover-streamer for call {call_id}: {e}")
      return False

  async def disconnect_from_streamer(self, call_id: str) -> None:
    """
    Disconnect from the external ringover-streamer.

    Args:
        call_id: Ringover call ID
    """
    try:
      logger.info(f"🔌 Disconnecting from ringover-streamer for call {call_id}")

      # Disconnect from the external ringover-streamer
      await self.streamer_client.disconnect_from_streamer(call_id)

      if call_id in self.active_streams:
        self.active_streams[call_id]["streamer_connected"] = False

      logger.info(f"✅ Disconnected from ringover-streamer for call {call_id}")

    except Exception as e:
      logger.error(
          f"Error disconnecting from ringover-streamer for call {call_id}: {e}")

  async def send_greeting(self, call_id: str) -> None:
    """
    Send initial greeting to the caller.

    Args:
        call_id: Ringover call ID
    """
    try:
      if call_id not in self.streamer_client.active_calls:
        logger.warning(
            f"Cannot send greeting: call {call_id} not connected to streamer")
        return

      greeting_message = {
          "event": "play",
          "file": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
      }

      websocket = self.streamer_client.active_calls[call_id]["websocket"]
      await websocket.send(json.dumps(greeting_message))
      logger.info(f"🎵 Sent greeting to call {call_id}")

    except Exception as e:
      logger.error(f"Failed to send greeting to call {call_id}: {e}")

  async def process_audio_chunk(self, call_id: str, audio_data: Dict[str, Any], agent_id: str) -> None:
    """
    Process an audio chunk from the caller.

    Args:
        call_id: Ringover call ID
        audio_data: Audio data from ringover-streamer
        agent_id: Agent handling the call
    """
    try:
      logger.debug(f"🎙️  Processing audio chunk for call {call_id}")

      # Check if streamer connection is active
      if call_id not in self.streamer_client.active_calls:
        logger.warning(
            f"Cannot process audio: call {call_id} not connected to streamer")
        return

      # Use AudioProcessor if available
      if self.audio_processor:
        # Process through STT->LLM->TTS pipeline
        response_audio_url = await self.audio_processor.process_audio_chunk(
            call_id, audio_data, agent_id
        )

        if response_audio_url:
          # Send audio response back to caller
          response_message = {
              "event": "play",
              "file": response_audio_url
          }

          websocket = self.streamer_client.active_calls[call_id]["websocket"]
          await websocket.send(json.dumps(response_message))
          logger.debug(f"🎵 Sent AI response audio to call {call_id}")
        else:
          logger.warning(f"No audio response generated for call {call_id}")
      else:
        # Fallback: send simple acknowledgment
        logger.warning(
            f"Audio processor not available for call {call_id}, using fallback")
        response_message = {
            "event": "play",
            "file": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav"
        }

        websocket = self.streamer_client.active_calls[call_id]["websocket"]
        await websocket.send(json.dumps(response_message))
      logger.debug(f"🎵 Sent response to call {call_id}")

    except Exception as e:
      logger.error(f"Failed to process audio chunk for call {call_id}: {e}")

  async def cleanup_stream(self, call_id: str) -> None:
    """
    Clean up streaming resources for a call.

    Args:
        call_id: Ringover call ID
    """
    try:
      logger.info(f"🧹 Cleaning up streaming for call {call_id}")

      # Disconnect from streamer
      await self.disconnect_from_streamer(call_id)

      # Close stream handler
      if call_id in self.active_streams:
        await self.streaming_service.close_stream(call_id)
        del self.active_streams[call_id]

      logger.info(f"✅ Streaming cleanup completed for call {call_id}")

    except Exception as e:
      logger.error(f"Error during streaming cleanup for call {call_id}: {e}")

  def get_stream_status(self, call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of a streaming session.

    Args:
        call_id: Ringover call ID

    Returns:
        Stream status dictionary or None if not found
    """
    return self.active_streams.get(call_id)
