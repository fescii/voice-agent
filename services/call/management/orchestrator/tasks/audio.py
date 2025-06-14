"""
Audio processing task for background execution.
Handles real-time audio processing and streaming coordination.
"""
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from core.logging.setup import get_logger

logger = get_logger(__name__)


class AudioProcessingTask:
  """
  Background task for processing audio streams from Ringover calls.
  Manages the complete audio pipeline: RTP -> STT -> LLM -> TTS -> Response.
  """

  def __init__(self, call_id: str, session_id: str, agent_id: str, streaming_manager):
    """
    Initialize the audio processing task.

    Args:
        call_id: Ringover call ID
        session_id: Internal session ID
        agent_id: Agent handling the call
        streaming_manager: StreamingManager instance
    """
    self.task_id = f"audio_processing_{call_id}"
    self.task_type = "audio_processing"
    self.priority = 1
    self.metadata = {
        "call_id": call_id,
        "session_id": session_id,
        "agent_id": agent_id
    }

    self.call_id = call_id
    self.session_id = session_id
    self.agent_id = agent_id
    self.streaming_manager = streaming_manager
    self.is_running = False
    self.created_at = datetime.now(timezone.utc)

  async def execute(self) -> Dict[str, Any]:
    """
    Execute the audio processing task.

    Returns:
        Task execution result
    """
    try:
      logger.info(f"🎵 Starting audio processing task for call {self.call_id}")
      self.is_running = True

      # Initialize streaming
      await self.streaming_manager.initialize_streaming(
          self.call_id,
          self.session_id,
          self.agent_id
      )

      # Connect to the external ringover-streamer
      connected = await self.streaming_manager.connect_to_streamer(self.call_id)

      if not connected:
        logger.error(
            f"❌ Failed to connect to ringover-streamer for call {self.call_id}")
        return {
            "success": False,
            "error": "Failed to connect to ringover-streamer",
            "call_id": self.call_id
        }

      # Send initial greeting
      await self.streaming_manager.send_greeting(self.call_id)

      # Start the audio processing loop
      await self._audio_processing_loop()

      return {
          "success": True,
          "call_id": self.call_id,
          "message": "Audio processing completed"
      }

    except Exception as e:
      logger.error(
          f"Audio processing task failed for call {self.call_id}: {e}")
      return {
          "success": False,
          "error": str(e),
          "call_id": self.call_id
      }
    finally:
      self.is_running = False
      await self._cleanup()

  async def _audio_processing_loop(self) -> None:
    """
    Main audio processing loop.
    Handles real-time audio from ringover-streamer.
    """
    try:
      logger.info(f"🎧 Starting audio processing loop for call {self.call_id}")

      # Get the WebSocket connection from the streamer client
      if self.call_id not in self.streaming_manager.streamer_client.active_calls:
        logger.error(f"No active streamer connection for call {self.call_id}")
        return

      websocket = self.streaming_manager.streamer_client.active_calls[self.call_id]["websocket"]

      # Process messages from ringover-streamer
      async for message in websocket:
        if not self.is_running:
          logger.info(f"Audio processing stopped for call {self.call_id}")
          break

        try:
          data = json.loads(message) if isinstance(message, str) else message
          logger.debug(
              f"📥 Received from ringover-streamer: {data.get('type', 'unknown')}")

          # Process different types of messages
          await self._handle_message(data)

        except json.JSONDecodeError:
          logger.warning(f"Received non-JSON message: {message}")
        except Exception as e:
          logger.error(f"Error processing message from ringover-streamer: {e}")

    except Exception as e:
      logger.error(
          f"Error in audio processing loop for call {self.call_id}: {e}")

  async def _handle_message(self, data: Dict[str, Any]) -> None:
    """
    Handle a message from ringover-streamer.

    Args:
        data: Message data
    """
    message_type = data.get("type") or data.get("event")

    if message_type == "audio":
      await self.streaming_manager.process_audio_chunk(
          self.call_id,
          data,
          self.agent_id
      )
    elif message_type == "call_started":
      logger.info(f"📞 Call {self.call_id} started - audio streaming active")
    elif message_type == "call_ended":
      logger.info(f"📞 Call {self.call_id} ended - stopping audio processing")
      self.is_running = False
    else:
      logger.debug(f"Unhandled message type: {message_type}")

  async def _cleanup(self) -> None:
    """Clean up resources when task completes."""
    try:
      logger.info(f"🧹 Cleaning up audio processing for call {self.call_id}")
      await self.streaming_manager.cleanup_stream(self.call_id)
      logger.info(
          f"✅ Audio processing cleanup completed for call {self.call_id}")
    except Exception as e:
      logger.error(
          f"Error during audio processing cleanup for call {self.call_id}: {e}")

  async def cancel(self) -> None:
    """Cancel the audio processing task."""
    logger.info(f"🛑 Cancelling audio processing task for call {self.call_id}")
    self.is_running = False
    await self._cleanup()

  def get_status(self) -> Dict[str, Any]:
    """
    Get the current status of the audio processing task.

    Returns:
        Status dictionary
    """
    return {
        "task_id": self.task_id,
        "call_id": self.call_id,
        "session_id": self.session_id,
        "agent_id": self.agent_id,
        "is_running": self.is_running,
        "task_type": self.task_type,
        "priority": self.priority
    }
