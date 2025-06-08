"""
Main Ringover WebSocket streamer that coordinates all streaming functionality.
"""
import asyncio
from typing import Optional

from core.logging.setup import get_logger
from core.config.providers.ringover import RingoverConfig
from .models import AudioHandler, EventHandler
from .connection import ConnectionManager
from .audio import AudioProcessor, AudioControlManager
from .messaging import MessageListener, MessageRouter
from .handlers import MessageHandler, ControlHandler, EventMessageHandler

logger = get_logger(__name__)


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

    # Initialize components
    self.connection_manager = ConnectionManager(config)
    self.audio_processor = AudioProcessor(self.connection_manager)
    self.audio_control = AudioControlManager(self.connection_manager)
    self.message_listener = MessageListener(self.connection_manager)

    # Initialize handlers
    self.message_handler = MessageHandler(
        self.connection_manager, self.audio_processor)
    self.control_handler = ControlHandler(self.connection_manager)
    self.event_handler = EventMessageHandler()

    # Will be initialized when event handler is set
    self.message_router: Optional[MessageRouter] = None

  def set_audio_handler(self, handler: AudioHandler):
    """
    Set the audio handler for processing incoming audio.

    Args:
        handler: Function to process incoming audio frames
    """
    self.audio_processor.set_audio_handler(handler)

  def set_event_handler(self, handler: EventHandler):
    """
    Set the event handler for processing incoming events.

    Args:
        handler: Function to process incoming events
    """
    self.event_handler.set_event_handler(handler)

    # Initialize message router if not already done
    if not self.message_router:
      self.message_router = MessageRouter(
          self.message_listener,
          handler
      )

  async def connect(self, call_id: str, auth_token: str) -> bool:
    """
    Connect to Ringover WebSocket for a specific call.

    Args:
        call_id: ID of the call to stream
        auth_token: Authentication token

    Returns:
        True if connection successful, False otherwise
    """
    success = await self.connection_manager.connect(call_id, auth_token)

    if success:
      # Initialize message router if not already done
      if not self.message_router:
        self.message_router = MessageRouter(self.audio_processor)

      # Start listening for messages
      asyncio.create_task(
          self.message_listener.start_listening(
              call_id, self.message_router.handle_message)
      )

    return success

  async def disconnect(self, call_id: str):
    """
    Disconnect from Ringover WebSocket.

    Args:
        call_id: ID of the call to disconnect
    """
    self.message_listener.stop_listening(call_id)
    await self.connection_manager.disconnect(call_id)

  async def send_audio(self, call_id: str, audio_data: bytes) -> bool:
    """
    Send audio data to Ringover.

    Args:
        call_id: ID of the call
        audio_data: Raw audio data to send

    Returns:
        True if sent successfully, False otherwise
    """
    return await self.audio_processor.send_audio(call_id, audio_data)

  async def send_control_message(self, call_id: str, action: str, data: Optional[dict] = None) -> bool:
    """
    Send a control message to Ringover.

    Args:
        call_id: ID of the call
        action: Control action (e.g., 'mute', 'unmute', 'hold')
        data: Additional control data

    Returns:
        True if sent successfully, False otherwise
    """
    return await self.audio_control._send_control_message(call_id, action, data)

  def is_connected(self) -> bool:
    """Check if WebSocket is connected."""
    return self.connection_manager.is_connected()

  def is_muted(self) -> bool:
    """Check if audio is muted."""
    return self.control_handler.is_muted

  async def mute(self, call_id: str) -> bool:
    """
    Mute audio for the call.

    Args:
        call_id: ID of the call to mute

    Returns:
        True if mute successful
    """
    return await self.control_handler.mute(call_id)

  async def unmute(self, call_id: str) -> bool:
    """
    Unmute audio for the call.

    Args:
        call_id: ID of the call to unmute

    Returns:
        True if unmute successful
    """
    return await self.control_handler.unmute(call_id)

  async def set_volume(self, call_id: str, volume: float) -> bool:
    """
    Set audio volume for the call.

    Args:
        call_id: ID of the call
        volume: Volume level (0.0 to 1.0)

    Returns:
        True if successful, False otherwise
    """
    return await self.control_handler.set_volume(call_id, volume)
