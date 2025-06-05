"""
WebSocket Connection Management
Handles individual WebSocket connections for audio streaming.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Set, Callable
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from enum import Enum

from core.logging import get_logger
from models.internal.callcontext import CallContext

logger = get_logger(__name__)


class ConnectionState(Enum):
  """WebSocket connection states"""
  CONNECTING = "connecting"
  CONNECTED = "connected"
  AUTHENTICATED = "authenticated"
  IN_CALL = "in_call"
  DISCONNECTED = "disconnected"
  ERROR = "error"


class AudioFormat(Enum):
  """Supported audio formats"""
  PCM_16000 = "pcm_16000"
  MULAW_8000 = "mulaw_8000"
  OPUS = "opus"


class WebSocketConnection:
  """Manages a single WebSocket connection"""

  def __init__(self, websocket: WebSocket, connection_id: str):
    self.websocket = websocket
    self.connection_id = connection_id
    self.state = ConnectionState.CONNECTING
    self.created_at = datetime.utcnow()
    self.last_activity = datetime.utcnow()

    # Connection metadata
    self.user_id: Optional[str] = None
    self.call_context: Optional[CallContext] = None
    self.audio_format = AudioFormat.PCM_16000
    self.metadata: Dict[str, Any] = {}

    # Event handlers
    self.message_handlers: Dict[str, Callable] = {}
    self.audio_handlers: Set[Callable] = set()
    self.disconnect_handlers: Set[Callable] = set()

    logger.info(f"WebSocket connection created: {connection_id}")

  async def accept(self) -> None:
    """Accept the WebSocket connection"""
    try:
      await self.websocket.accept()
      self.state = ConnectionState.CONNECTED
      self.last_activity = datetime.utcnow()
      logger.info(f"WebSocket connection accepted: {self.connection_id}")
    except Exception as e:
      logger.error(
          f"Failed to accept WebSocket connection {self.connection_id}: {str(e)}")
      self.state = ConnectionState.ERROR
      raise

  async def authenticate(self, token: str) -> bool:
    """Authenticate the WebSocket connection"""
    try:
      # TODO: Implement actual authentication logic
      # This would validate the JWT token and extract user info

      # Placeholder authentication
      if token and len(token) > 10:
        self.state = ConnectionState.AUTHENTICATED
        self.user_id = f"user_{hash(token) % 10000}"
        logger.info(
            f"WebSocket connection authenticated: {self.connection_id}")
        return True

      return False
    except Exception as e:
      logger.error(f"Authentication failed for {self.connection_id}: {str(e)}")
      return False

  async def send_message(self, message_type: str, data: Dict[str, Any]) -> None:
    """Send a structured message to the client"""
    try:
      message = {
          "type": message_type,
          "timestamp": datetime.utcnow().isoformat(),
          "data": data
      }
      await self.websocket.send_text(json.dumps(message))
      self.last_activity = datetime.utcnow()
      logger.debug(f"Sent message to {self.connection_id}: {message_type}")
    except Exception as e:
      logger.error(f"Failed to send message to {self.connection_id}: {str(e)}")
      await self._handle_error(e)

  async def send_audio(self, audio_data: bytes) -> None:
    """Send audio data to the client"""
    try:
      await self.websocket.send_bytes(audio_data)
      self.last_activity = datetime.utcnow()
      logger.debug(
          f"Sent audio data to {self.connection_id}: {len(audio_data)} bytes")
    except Exception as e:
      logger.error(f"Failed to send audio to {self.connection_id}: {str(e)}")
      await self._handle_error(e)

  async def receive_message(self) -> Optional[Dict[str, Any]]:
    """Receive and parse a message from the client"""
    try:
      data = await self.websocket.receive_text()
      self.last_activity = datetime.utcnow()

      try:
        message = json.loads(data)
        logger.debug(
            f"Received message from {self.connection_id}: {message.get('type', 'unknown')}")
        return message
      except json.JSONDecodeError:
        logger.warning(f"Invalid JSON from {self.connection_id}: {data[:100]}")
        return None

    except WebSocketDisconnect:
      logger.info(f"WebSocket disconnected: {self.connection_id}")
      self.state = ConnectionState.DISCONNECTED
      return None
    except Exception as e:
      logger.error(
          f"Error receiving message from {self.connection_id}: {str(e)}")
      await self._handle_error(e)
      return None

  async def receive_audio(self) -> Optional[bytes]:
    """Receive audio data from the client"""
    try:
      data = await self.websocket.receive_bytes()
      self.last_activity = datetime.utcnow()
      logger.debug(
          f"Received audio from {self.connection_id}: {len(data)} bytes")

      # Notify audio handlers
      for handler in self.audio_handlers:
        try:
          await handler(data)
        except Exception as e:
          logger.error(f"Audio handler error: {str(e)}")

      return data
    except WebSocketDisconnect:
      logger.info(
          f"WebSocket disconnected during audio receive: {self.connection_id}")
      self.state = ConnectionState.DISCONNECTED
      return None
    except Exception as e:
      logger.error(
          f"Error receiving audio from {self.connection_id}: {str(e)}")
      await self._handle_error(e)
      return None

  def add_message_handler(self, message_type: str, handler: Callable) -> None:
    """Add a handler for specific message types"""
    self.message_handlers[message_type] = handler
    logger.debug(f"Added message handler for {message_type}")

  def add_audio_handler(self, handler: Callable) -> None:
    """Add a handler for audio data"""
    self.audio_handlers.add(handler)
    logger.debug(f"Added audio handler")

  def add_disconnect_handler(self, handler: Callable) -> None:
    """Add a handler for disconnection events"""
    self.disconnect_handlers.add(handler)
    logger.debug(f"Added disconnect handler")

  async def start_call(self, call_context: CallContext) -> None:
    """Start a call session"""
    self.call_context = call_context
    self.state = ConnectionState.IN_CALL

    await self.send_message("call_started", {
        "call_id": call_context.call_id,
        "session_id": call_context.session_id,
        "audio_format": self.audio_format.value
    })

    logger.info(
        f"Call started for connection {self.connection_id}: {call_context.call_id}")

  async def end_call(self) -> None:
    """End the current call session"""
    if self.call_context:
      call_id = self.call_context.call_id
      self.call_context = None
      self.state = ConnectionState.AUTHENTICATED

      await self.send_message("call_ended", {
          "call_id": call_id,
          "timestamp": datetime.utcnow().isoformat()
      })

      logger.info(f"Call ended for connection {self.connection_id}: {call_id}")

  async def close(self, code: int = 1000, reason: str = "Normal closure") -> None:
    """Close the WebSocket connection"""
    try:
      self.state = ConnectionState.DISCONNECTED

      # Notify disconnect handlers
      for handler in self.disconnect_handlers:
        try:
          await handler(self)
        except Exception as e:
          logger.error(f"Disconnect handler error: {str(e)}")

      await self.websocket.close(code=code, reason=reason)
      logger.info(f"WebSocket connection closed: {self.connection_id}")

    except Exception as e:
      logger.error(f"Error closing WebSocket {self.connection_id}: {str(e)}")

  async def _handle_error(self, error: Exception) -> None:
    """Handle connection errors"""
    self.state = ConnectionState.ERROR

    # Send error message to client if possible
    try:
      await self.send_message("error", {
          "message": "Connection error occurred",
          "code": "WEBSOCKET_ERROR"
      })
    except:
      pass  # Connection might be broken

    # Close connection
    await self.close(code=1011, reason="Internal error")

  def is_active(self) -> bool:
    """Check if connection is active"""
    return self.state in [
        ConnectionState.CONNECTED,
        ConnectionState.AUTHENTICATED,
        ConnectionState.IN_CALL
    ]

  def get_info(self) -> Dict[str, Any]:
    """Get connection information"""
    return {
        "connection_id": self.connection_id,
        "state": self.state.value,
        "user_id": self.user_id,
        "call_id": self.call_context.call_id if self.call_context else None,
        "created_at": self.created_at.isoformat(),
        "last_activity": self.last_activity.isoformat(),
        "audio_format": self.audio_format.value,
        "metadata": self.metadata
    }


class ConnectionManager:
  """Manages multiple WebSocket connections"""

  def __init__(self):
    self.connections: Dict[str, WebSocketConnection] = {}
    # user_id -> connection_ids
    self.user_connections: Dict[str, Set[str]] = {}
    # call_id -> connection_ids
    self.call_connections: Dict[str, Set[str]] = {}

    logger.info("WebSocket Connection Manager initialized")

  def add_connection(self, connection: WebSocketConnection) -> None:
    """Add a new connection"""
    self.connections[connection.connection_id] = connection
    logger.info(f"Added connection to manager: {connection.connection_id}")

  def remove_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
    """Remove a connection"""
    connection = self.connections.pop(connection_id, None)
    if connection:
      # Remove from user mapping
      if connection.user_id and connection.user_id in self.user_connections:
        self.user_connections[connection.user_id].discard(connection_id)
        if not self.user_connections[connection.user_id]:
          del self.user_connections[connection.user_id]

      # Remove from call mapping
      if connection.call_context and connection.call_context.call_id in self.call_connections:
        self.call_connections[connection.call_context.call_id].discard(
            connection_id)
        if not self.call_connections[connection.call_context.call_id]:
          del self.call_connections[connection.call_context.call_id]

      logger.info(f"Removed connection from manager: {connection_id}")

    return connection

  def get_connection(self, connection_id: str) -> Optional[WebSocketConnection]:
    """Get a connection by ID"""
    return self.connections.get(connection_id)

  def get_user_connections(self, user_id: str) -> Set[WebSocketConnection]:
    """Get all connections for a user"""
    connection_ids = self.user_connections.get(user_id, set())
    return {self.connections[cid] for cid in connection_ids if cid in self.connections}

  def get_call_connections(self, call_id: str) -> Set[WebSocketConnection]:
    """Get all connections for a call"""
    connection_ids = self.call_connections.get(call_id, set())
    return {self.connections[cid] for cid in connection_ids if cid in self.connections}

  async def associate_user(self, connection_id: str, user_id: str) -> None:
    """Associate a connection with a user"""
    if connection_id in self.connections:
      connection = self.connections[connection_id]
      connection.user_id = user_id

      if user_id not in self.user_connections:
        self.user_connections[user_id] = set()
      self.user_connections[user_id].add(connection_id)

      logger.info(f"Associated connection {connection_id} with user {user_id}")

  async def associate_call(self, connection_id: str, call_id: str) -> None:
    """Associate a connection with a call"""
    if connection_id in self.connections:
      if call_id not in self.call_connections:
        self.call_connections[call_id] = set()
      self.call_connections[call_id].add(connection_id)

      logger.info(f"Associated connection {connection_id} with call {call_id}")

  async def broadcast_to_call(self, call_id: str, message_type: str, data: Dict[str, Any]) -> None:
    """Broadcast a message to all connections in a call"""
    connections = self.get_call_connections(call_id)
    if connections:
      await asyncio.gather(
          *[conn.send_message(message_type, data) for conn in connections],
          return_exceptions=True
      )
      logger.debug(
          f"Broadcasted {message_type} to {len(connections)} connections in call {call_id}")

  async def cleanup_inactive_connections(self, timeout_minutes: int = 30) -> int:
    """Clean up inactive connections"""
    cutoff = datetime.utcnow().timestamp() - (timeout_minutes * 60)
    inactive_connections = []

    for connection in self.connections.values():
      if connection.last_activity.timestamp() < cutoff:
        inactive_connections.append(connection.connection_id)

    for connection_id in inactive_connections:
      connection = self.remove_connection(connection_id)
      if connection:
        await connection.close(code=1001, reason="Connection timeout")

    if inactive_connections:
      logger.info(
          f"Cleaned up {len(inactive_connections)} inactive connections")

    return len(inactive_connections)

  def get_stats(self) -> Dict[str, Any]:
    """Get connection statistics"""
    total_connections = len(self.connections)
    authenticated_connections = sum(1 for conn in self.connections.values()
                                    if conn.state == ConnectionState.AUTHENTICATED)
    active_calls = len(self.call_connections)

    return {
        "total_connections": total_connections,
        "authenticated_connections": authenticated_connections,
        "active_calls": active_calls,
        "users_connected": len(self.user_connections),
        "average_connections_per_user": (
            total_connections / len(self.user_connections)
            if self.user_connections else 0
        )
    }


# Global connection manager instance
connection_manager = ConnectionManager()
