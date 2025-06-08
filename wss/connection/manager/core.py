"""
WebSocket connection manager.
"""

import asyncio
from typing import Dict, Set, Optional, Any
from datetime import datetime, timezone

from core.logging import get_logger
from ..session.websocket import WebSocketConnection
from ..models.enums import ConnectionState

logger = get_logger(__name__)


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
    cutoff = datetime.now(timezone.utc).timestamp() - (timeout_minutes * 60)
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
