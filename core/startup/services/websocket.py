"""
WebSocket s  def __init__(self):
    super().__init__("websocket", is_critical=True)vice startup initialization.
Handles WebSocket connection management and handlers.
"""
from typing import Dict, Any

from .base import BaseStartupService
from core.logging.setup import get_logger

logger = get_logger(__name__)


class WebSocketService(BaseStartupService):
  """WebSocket service startup handler."""

  def __init__(self):
    super().__init__("websocket", is_critical=False)

  async def initialize(self, context) -> Dict[str, Any]:
    """Initialize WebSocket services."""
    try:
      # Import the global WebSocket handlers instance
      from wss.handlers.instances import websocket_handlers

      # Get WebSocket configuration
      ws_config = context.configuration.websocket

      logger.info("WebSocket services initialized successfully")

      return {
          "connection_manager": websocket_handlers,
          "orchestrator": websocket_handlers,
          "max_connections": getattr(ws_config, 'max_connections', 1000),
          "ping_interval": getattr(ws_config, 'ping_interval', 30),
          "status": "ready"
      }

    except Exception as e:
      logger.error(f"Failed to initialize WebSocket service: {e}")
      raise

  async def cleanup(self, context) -> None:
    """Cleanup WebSocket services."""
    try:
      logger.info("Cleaning up WebSocket service...")
      # WebSocket connections are typically cleaned up automatically
      # when the application shuts down

    except Exception as e:
      logger.error(f"Error cleaning up WebSocket service: {e}")
