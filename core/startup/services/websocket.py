"""
WebSocket service startup initialization.
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
      # Initialize WebSocket handlers orchestrator
      from wss.handlers import WebSocketHandlers

      # Get WebSocket configuration
      ws_config = context.configuration.get("websocket", {})

      # Initialize WebSocket handlers orchestrator
      orchestrator = WebSocketHandlers()

      # Get the connection manager from the orchestrator
      connection_manager = orchestrator.connection_manager

      logger.info("WebSocket services initialized successfully")

      return {
          "connection_manager": connection_manager,
          "orchestrator": orchestrator,
          "max_connections": ws_config.get("max_connections", 1000),
          "ping_interval": ws_config.get("ping_interval", 30),
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
