"""
WebSocket connection orchestration manager.
"""

from wss.connection import WebSocketConnection, ConnectionManager
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ConnectionOrchestrator:
  """Orchestrates WebSocket connections using initialized handlers."""

  def __init__(self, handler_registry):
    self.handler_registry = handler_registry
    self.connection_manager = ConnectionManager()

  def initialize(self):
    """Initialize the connection manager with handlers."""
    # The ConnectionManager doesn't need initialization with handlers
    # as it manages connections directly
    logger.info("Connection orchestrator initialized")

  async def handle_connection(self, connection: WebSocketConnection) -> None:
    """Handle a new WebSocket connection."""
    # Add the connection to the manager
    self.connection_manager.add_connection(connection)

    # Set up handlers from registry if needed
    if hasattr(self.handler_registry, 'setup_connection_handlers'):
      self.handler_registry.setup_connection_handlers(connection)
