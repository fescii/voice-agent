"""
WebSocket connection management for Ringover streaming.
"""
import asyncio
from typing import Dict, Optional, Any
import json

from core.logging.setup import get_logger
from core.config.providers.ringover import RingoverConfig

logger = get_logger(__name__)


class ConnectionManager:
  """Manages WebSocket connections to Ringover."""

  def __init__(self, config: RingoverConfig):
    self.config = config
    self.websocket: Optional[Any] = None
    self.connected = False
    self.active_streams: Dict[str, bool] = {}
    self.muted = False

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
    try:
      if call_id in self.active_streams:
        del self.active_streams[call_id]

      if self.websocket and not self.websocket.closed:
        await self.websocket.close()
        logger.info(f"Disconnected from Ringover WebSocket for call {call_id}")

      self.connected = False

    except Exception as e:
      logger.error(f"Error disconnecting from WebSocket: {e}")

  def is_connected(self) -> bool:
    """Check if WebSocket is connected."""
    if not self.connected or not self.websocket:
      return False
    try:
      return not self.websocket.closed
    except AttributeError:
      return False

  def is_muted(self) -> bool:
    """Check if audio is muted."""
    return self.muted

  async def send_message(self, message: dict) -> bool:
    """
    Send message to WebSocket.

    Args:
        message: Message to send

    Returns:
        True if sent successfully
    """
    if not self.is_connected() or not self.websocket:
      logger.error("Cannot send message: WebSocket not connected")
      return False

    try:
      await self.websocket.send(json.dumps(message))
      return True
    except Exception as e:
      logger.error(f"Failed to send WebSocket message: {e}")
      return False

  async def receive_message(self) -> Optional[dict]:
    """
    Receive message from WebSocket.

    Returns:
        Received message or None if error
    """
    if not self.is_connected() or not self.websocket:
      return None

    try:
      raw_message = await self.websocket.recv()
      return json.loads(raw_message)
    except Exception as e:
      logger.error(f"Failed to receive WebSocket message: {e}")
      return None
