"""
Ringover WebSocket streaming handler.
"""
import asyncio
import json
from typing import Dict, Any, Optional, Callable, Awaitable, TYPE_CHECKING
from dataclasses import dataclass
import uuid

if TYPE_CHECKING:
  import websockets

from core.logging.setup import get_logger
from core.config.registry import config_registry
from core.config.providers.ringover import RingoverConfig

logger = get_logger(__name__)


@dataclass
class AudioFrame:
  """Audio frame data structure."""
  call_id: str
  audio_data: bytes
  format: str = "pcm"
  sample_rate: int = 16000
  channels: int = 1
  timestamp: Optional[float] = None


AudioHandler = Callable[[AudioFrame], Awaitable[Optional[bytes]]]
EventHandler = Callable[[Dict[str, Any]], Awaitable[None]]


class RingoverWebSocketStreamer:
  """
  Ringover WebSocket streaming client for real-time audio.

  Handles bidirectional audio streaming between Ringover and the
  voice agent system for real-time conversation processing.
  """

  def __init__(self, config: RingoverConfig):
    """
    Initialize Ringover WebSocket streamer.

    Args:
        config: Ringover configuration
    """
    self.config = config
    self.websocket: Optional[Any] = None
    self.connected = False
    self.audio_handler: Optional[AudioHandler] = None
    self.event_handler: Optional[EventHandler] = None
    self.active_streams: Dict[str, bool] = {}

  def set_audio_handler(self, handler: AudioHandler):
    """
    Set the audio processing handler.

    Args:
        handler: Function to process incoming audio frames
    """
    self.audio_handler = handler

  def set_event_handler(self, handler: EventHandler):
    """
    Set the event processing handler.

    Args:
        handler: Function to process incoming events
    """
    self.event_handler = handler

  async def connect(self, call_id: str, auth_token: str) -> bool:
    """
    Connect to Ringover WebSocket for a specific call.

    Args:
        call_id: ID of the call to stream
        auth_token: Authentication token

    Returns:
        True if connection successful, False otherwise
    """
    uri = f"{self.config.websocket_url}/stream/{call_id}"
    headers = {
        "Authorization": f"Bearer {auth_token}",
        "X-Call-ID": call_id
    }

    try:
      # Import websockets dynamically to avoid import errors
      import websockets

      self.websocket = await websockets.connect(
          uri,
          extra_headers=headers,
          ping_interval=30,
          ping_timeout=10
      )
      self.connected = True
      self.active_streams[call_id] = True

      logger.info(f"Connected to Ringover WebSocket for call {call_id}")

      # Start listening for messages
      asyncio.create_task(self._listen_loop(call_id))

      return True

    except Exception as e:
      logger.error(f"Failed to connect to Ringover WebSocket: {e}")
      return False

  async def disconnect(self, call_id: str):
    """
    Disconnect from Ringover WebSocket.

    Args:
        call_id: ID of the call to disconnect
    """
    if call_id in self.active_streams:
      self.active_streams[call_id] = False

    if self.websocket and self.connected:
      await self.websocket.close()
      self.connected = False
      logger.info(f"Disconnected from Ringover WebSocket for call {call_id}")

  async def send_audio(self, call_id: str, audio_data: bytes) -> bool:
    """
    Send audio data to Ringover.

    Args:
        call_id: ID of the call
        audio_data: Raw audio data to send

    Returns:
        True if sent successfully, False otherwise
    """
    if not self.websocket or not self.connected:
      logger.warning("WebSocket not connected")
      return False

    message = {
        "type": "audio",
        "call_id": call_id,
        "data": audio_data.hex(),  # Convert bytes to hex string
        "format": "pcm",
        "sample_rate": 16000,
        "channels": 1
    }

    try:
      await self.websocket.send(json.dumps(message))
      return True
    except Exception as e:
      logger.error(f"Failed to send audio: {e}")
      return False

  async def send_control_message(self, call_id: str, action: str, data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Send a control message to Ringover.

    Args:
        call_id: ID of the call
        action: Control action (e.g., 'mute', 'unmute', 'hold')
        data: Additional control data

    Returns:
        True if sent successfully, False otherwise
    """
    if not self.websocket or not self.connected:
      logger.warning("WebSocket not connected")
      return False

    message = {
        "type": "control",
        "call_id": call_id,
        "action": action,
        "data": data or {}
    }

    try:
      await self.websocket.send(json.dumps(message))
      return True
    except Exception as e:
      logger.error(f"Failed to send control message: {e}")
      return False

  async def _listen_loop(self, call_id: str):
    """
    Listen for incoming WebSocket messages.

    Args:
        call_id: ID of the call being streamed
    """
    try:
      if not self.websocket:
        return

      async for message in self.websocket:
        if not self.active_streams.get(call_id, False):
          break

        try:
          data = json.loads(message)
          await self._handle_message(call_id, data)
        except json.JSONDecodeError:
          logger.warning("Received invalid JSON message")
        except Exception as e:
          logger.error(f"Error handling message: {e}")

    except Exception as e:
      # Import websockets for exception handling
      try:
        import websockets
        if isinstance(e, websockets.exceptions.ConnectionClosed):
          logger.info(f"WebSocket connection closed for call {call_id}")
        else:
          logger.error(f"Error in listen loop: {e}")
      except ImportError:
        logger.error(f"Error in listen loop: {e}")
    finally:
      self.connected = False
      if call_id in self.active_streams:
        del self.active_streams[call_id]

  async def _handle_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming WebSocket message.

    Args:
        call_id: ID of the call
        data: Message data
    """
    message_type = data.get("type")

    if message_type == "audio":
      await self._handle_audio_message(call_id, data)
    elif message_type == "event":
      await self._handle_event_message(call_id, data)
    elif message_type == "control":
      await self._handle_control_message(call_id, data)
    else:
      logger.warning(f"Unknown message type: {message_type}")

  async def _handle_audio_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming audio message.

    Args:
        call_id: ID of the call
        data: Audio message data
    """
    if not self.audio_handler:
      return

    try:
      # Convert hex string back to bytes
      audio_data = bytes.fromhex(data.get("data", ""))

      audio_frame = AudioFrame(
          call_id=call_id,
          audio_data=audio_data,
          format=data.get("format", "pcm"),
          sample_rate=data.get("sample_rate", 16000),
          channels=data.get("channels", 1),
          timestamp=data.get("timestamp")
      )

      # Process audio and get response
      response_audio = await self.audio_handler(audio_frame)

      # Send response audio back if available
      if response_audio:
        await self.send_audio(call_id, response_audio)

    except Exception as e:
      logger.error(f"Error handling audio message: {e}")

  async def _handle_event_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming event message.

    Args:
        call_id: ID of the call
        data: Event message data
    """
    if self.event_handler:
      event_data = {
          "call_id": call_id,
          "event_type": data.get("event"),
          "data": data.get("data", {})
      }
      await self.event_handler(event_data)

  async def _handle_control_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming control message.

    Args:
        call_id: ID of the call
        data: Control message data
    """
    action = data.get("action")
    logger.info(f"Received control message for call {call_id}: {action}")

    # Handle specific control actions
    if action == "end_stream":
      await self.disconnect(call_id)

  @property
  def is_connected(self) -> bool:
    """Check if WebSocket is connected."""
    return self.connected

  @property
  def is_muted(self) -> bool:
    """Check if audio is muted."""
    return getattr(self, '_muted', False)

  async def mute(self, call_id: str) -> bool:
    """
    Mute audio for the call.

    Args:
        call_id: ID of the call to mute

    Returns:
        True if successful, False otherwise  
    """
    success = await self.send_control_message(call_id, "mute")
    if success:
      self._muted = True
    return success

  async def unmute(self, call_id: str) -> bool:
    """
    Unmute audio for the call.

    Args:
        call_id: ID of the call to unmute

    Returns:
        True if successful, False otherwise
    """
    success = await self.send_control_message(call_id, "unmute")
    if success:
      self._muted = False
    return success

  async def set_volume(self, call_id: str, volume: float) -> bool:
    """
    Set audio volume for the call.

    Args:
        call_id: ID of the call
        volume: Volume level (0.0 to 1.0)

    Returns:
        True if successful, False otherwise
    """
    return await self.send_control_message(call_id, "set_volume", {"volume": volume})
