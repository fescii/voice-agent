"""
WebSocket authentication handlers.
"""

from datetime import datetime
from typing import Dict, Any

from wss.connection import WebSocketConnection
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AuthHandler:
  """Handles WebSocket authentication."""

  async def handle_authentication(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle authentication message"""
    try:
      token = data.get("token")
      if not token:
        await connection.send_message("auth_error", {
            "message": "Token is required",
            "code": "MISSING_TOKEN"
        })
        return

      # Authenticate the connection
      if await connection.authenticate(token):
        await connection.send_message("auth_success", {
            "user_id": connection.user_id,
            "authenticated_at": datetime.utcnow().isoformat()
        })
        logger.info(
            f"Successfully authenticated connection {connection.connection_id}")
      else:
        await connection.send_message("auth_error", {
            "message": "Invalid token",
            "code": "INVALID_TOKEN"
        })

    except Exception as e:
      logger.error(
          f"Authentication error for {connection.connection_id}: {str(e)}")
      await connection.send_message("auth_error", {
          "message": "Authentication failed",
          "code": "AUTH_FAILED"
      })
