"""
Message handling and listening for WebSocket streams.
"""
import asyncio
import json
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from ..models import EventHandler
from ..connection import ConnectionManager

logger = get_logger(__name__)


class MessageListener:
  """Handles listening for incoming WebSocket messages."""

  def __init__(self, connection_manager: ConnectionManager):
    self.connection_manager = connection_manager
    self.active_listeners: Dict[str, bool] = {}

  async def start_listening(self, call_id: str, message_handler):
    """
    Start listening for incoming WebSocket messages.

    Args:
        call_id: ID of the call being streamed
        message_handler: Function to handle incoming messages
    """
    self.active_listeners[call_id] = True

    try:
      while self.active_listeners.get(call_id, False) and self.connection_manager.is_connected():
        message = await self.connection_manager.receive_message()
        if message:
          await message_handler(call_id, message)
        else:
          # Connection lost
          break

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
      if call_id in self.active_listeners:
        del self.active_listeners[call_id]

  def stop_listening(self, call_id: str):
    """Stop listening for a specific call."""
    if call_id in self.active_listeners:
      self.active_listeners[call_id] = False


class MessageRouter:
  """Routes incoming messages to appropriate handlers."""

  def __init__(self, audio_processor, event_handler: Optional[EventHandler] = None):
    self.audio_processor = audio_processor
    self.event_handler = event_handler

  async def handle_message(self, call_id: str, data: Dict[str, Any]):
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
    """Handle incoming audio message."""
    await self.audio_processor.process_incoming_audio(call_id, data)

  async def _handle_event_message(self, call_id: str, data: Dict[str, Any]):
    """Handle incoming event message."""
    if self.event_handler:
      try:
        await self.event_handler(data)
      except Exception as e:
        logger.error(f"Event handler failed: {e}")
    else:
      logger.debug(
          f"Received event for call {call_id}: {data.get('event', 'unknown')}")

  async def _handle_control_message(self, call_id: str, data: Dict[str, Any]):
    """Handle incoming control message."""
    action = data.get("action")
    logger.info(f"Received control message for call {call_id}: {action}")

    # Handle control responses/acknowledgments
    if action == "mute_ack":
      logger.info(f"Mute acknowledged for call {call_id}")
    elif action == "unmute_ack":
      logger.info(f"Unmute acknowledged for call {call_id}")
    elif action == "status":
      status = data.get("data", {}).get("status")
      logger.info(f"Call {call_id} status: {status}")
    else:
      logger.debug(f"Unhandled control action: {action}")
