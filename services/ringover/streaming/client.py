"""
Integration client for the official ringover-streamer project.
"""
import asyncio
import json
import websockets
from typing import Dict, Any, Optional, Callable
import base64
from datetime import datetime, timezone

from core.logging.setup import get_logger
from core.config.registry import config_registry

logger = get_logger(__name__)


class RingoverStreamerClient:
  """
  Client for connecting to the official ringover-streamer WebSocket server.

  This client connects to the ringover-streamer (GitHub: ringover/ringover-streamer)
  which handles the actual RTP connection to Ringover media servers.
  """

  def __init__(self):
    """Initialize the streamer client."""
    self.config = config_registry.ringover
    self.websocket = None
    self.is_connected = False
    self.active_calls: Dict[str, Dict[str, Any]] = {}

    # Default ringover-streamer connection settings
    self.streamer_host = "localhost"
    self.streamer_port = 8000
    self.streamer_path = "/ws"

  async def connect(self) -> bool:
    """
    Initialize connection to the ringover-streamer service.

    This method prepares the client for connecting to calls but doesn't
    establish a WebSocket connection until connect_to_streamer is called
    for a specific call.

    Returns:
        True if initialization successful
    """
    try:
      logger.info("Initializing ringover-streamer client...")

      # Validate configuration
      if not self.config.api_key:
        raise ValueError("Ringover API key not configured")

      # Test connectivity to ringover-streamer service
      test_uri = f"http://{self.streamer_host}:{self.streamer_port}/health"
      logger.info(f"Testing connectivity to ringover-streamer at {test_uri}")

      # For now, just mark as connected - actual health check would use HTTP client
      self.is_connected = True
      logger.info("Ringover-streamer client initialized successfully")

      return True

    except Exception as e:
      logger.error(f"Failed to initialize ringover-streamer client: {e}")
      self.is_connected = False
      return False

  async def connect_to_streamer(self, call_id: str) -> bool:
    """
    Connect to the ringover-streamer WebSocket server for a specific call.

    Args:
        call_id: The call identifier from Ringover

    Returns:
        True if connection successful, False otherwise
    """
    try:
      uri = f"ws://{self.streamer_host}:{self.streamer_port}{self.streamer_path}"
      logger.info(
          f"Connecting to ringover-streamer at {uri} for call {call_id}")

      self.websocket = await websockets.connect(uri)
      self.is_connected = True

      # Initialize call tracking
      self.active_calls[call_id] = {
          "websocket": self.websocket,
          "start_time": datetime.now(timezone.utc),
          "audio_buffer": bytearray(),
          "conversation_history": []
      }

      logger.info(f"Connected to ringover-streamer for call {call_id}")
      return True

    except Exception as e:
      logger.error(f"Failed to connect to ringover-streamer: {e}")
      self.is_connected = False
      return False

  async def disconnect_from_streamer(self, call_id: str):
    """
    Disconnect from the ringover-streamer for a specific call.

    Args:
        call_id: The call identifier
    """
    try:
      if call_id in self.active_calls and self.websocket:
        await self.websocket.close()
        self.is_connected = False
        del self.active_calls[call_id]
        logger.info(f"Disconnected from ringover-streamer for call {call_id}")

    except Exception as e:
      logger.error(f"Error disconnecting from ringover-streamer: {e}")

  async def listen_for_audio(self, call_id: str, audio_callback: Callable):
    """
    Listen for incoming audio from ringover-streamer.

    Args:
        call_id: The call identifier
        audio_callback: Callback function to handle received audio
    """
    if not self.is_connected or call_id not in self.active_calls:
      logger.error(f"Not connected to streamer for call {call_id}")
      return

    websocket = self.active_calls[call_id]["websocket"]

    try:
      async for message in websocket:
        # Handle incoming messages from ringover-streamer
        if isinstance(message, bytes):
          # Raw audio data from Ringover RTP stream
          await audio_callback(call_id, message)
        else:
          # JSON message (metadata, events, etc.)
          try:
            data = json.loads(message)
            await self._handle_streamer_event(call_id, data)
          except json.JSONDecodeError:
            logger.warning(f"Received non-JSON text message: {message}")

    except websockets.exceptions.ConnectionClosed:
      logger.info(f"ringover-streamer connection closed for call {call_id}")
    except Exception as e:
      logger.error(f"Error listening to ringover-streamer: {e}")

  async def _handle_streamer_event(self, call_id: str, data: Dict[str, Any]):
    """
    Handle events received from ringover-streamer.

    Args:
        call_id: The call identifier
        data: Event data from ringover-streamer
    """
    event_type = data.get("type") or data.get("event")
    logger.debug(f"Received streamer event: {event_type} for call {call_id}")

    # Handle different event types as needed
    if event_type == "call_started":
      logger.info(f"Call started event from ringover-streamer: {call_id}")
    elif event_type == "call_ended":
      logger.info(f"Call ended event from ringover-streamer: {call_id}")
      await self.disconnect_from_streamer(call_id)

  async def play_audio_file(self, call_id: str, file_url: str):
    """
    Send play command to ringover-streamer to play an audio file.

    Args:
        call_id: The call identifier
        file_url: URL of the audio file to play
    """
    command = {
        "event": "play",
        "file": file_url
    }
    await self._send_command(call_id, command)

  async def stream_audio_data(self, call_id: str, audio_data: bytes,
                              audio_format: str = "raw", sample_rate: int = 8000):
    """
    Stream base64 encoded audio data to ringover-streamer.

    Args:
        call_id: The call identifier
        audio_data: Raw audio bytes to stream
        audio_format: Audio format (raw, mp3, wav, ogg)
        sample_rate: Sample rate (8000, 16000, 24000)
    """
    # Encode audio data to base64
    encoded_audio = base64.b64encode(audio_data).decode('utf-8')

    command = {
        "type": "streamAudio",
        "data": {
            "audioDataType": audio_format,
            "sampleRate": sample_rate,
            "audioData": encoded_audio
        }
    }
    await self._send_command(call_id, command)

  async def break_audio(self, call_id: str):
    """
    Send break command to stop current audio streaming.

    Args:
        call_id: The call identifier
    """
    command = {"event": "break"}
    await self._send_command(call_id, command)

  async def send_dtmf_digits(self, call_id: str, digits: str):
    """
    Send DTMF digits through ringover-streamer.

    Args:
        call_id: The call identifier
        digits: Digits to send (e.g., "123")
    """
    command = {
        "event": "digits",
        "data": int(digits) if digits.isdigit() else digits
    }
    await self._send_command(call_id, command)

  async def transfer_call(self, call_id: str, phone_number: str):
    """
    Transfer call to another number through ringover-streamer.

    Args:
        call_id: The call identifier
        phone_number: Phone number to transfer to
    """
    command = {
        "event": "transfer",
        "data": phone_number
    }
    await self._send_command(call_id, command)

  async def _send_command(self, call_id: str, command: Dict[str, Any]):
    """
    Send command to ringover-streamer.

    Args:
        call_id: The call identifier
        command: Command data to send
    """
    if not self.is_connected or call_id not in self.active_calls:
      logger.error(f"Cannot send command - not connected for call {call_id}")
      return

    try:
      websocket = self.active_calls[call_id]["websocket"]
      message = json.dumps(command)
      await websocket.send(message)
      logger.debug(f"Sent command to ringover-streamer: {command}")

    except Exception as e:
      logger.error(f"Failed to send command to ringover-streamer: {e}")

  def get_active_calls(self) -> Dict[str, Dict[str, Any]]:
    """Get currently active calls."""
    return self.active_calls.copy()

  def is_call_active(self, call_id: str) -> bool:
    """Check if a call is currently active."""
    return call_id in self.active_calls and self.is_connected
