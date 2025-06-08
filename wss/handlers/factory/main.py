"""
Main WebSocket handlers factory.
"""

from ..services.initializer import ServiceInitializer
from ..initialization.handlers import HandlerInitializer
from ..mapping.registry import HandlerRegistry
from ..orchestration.manager import ConnectionOrchestrator
from core.logging.setup import get_logger

logger = get_logger(__name__)


class HandlersFactory:
  """Factory for creating and configuring WebSocket handlers."""

  def __init__(self):
    self.service_initializer = None
    self.handler_initializer = None
    self.handler_registry = None
    self.connection_orchestrator = None

  def create(self):
    """Create and initialize all handler components."""
    # Initialize services
    self.service_initializer = ServiceInitializer()
    self.service_initializer.initialize()

    # Initialize handlers
    services = self.service_initializer.get_services()
    self.handler_initializer = HandlerInitializer(services)
    self.handler_initializer.initialize()

    # Setup handler registry
    handlers = self.handler_initializer.get_handlers()
    self.handler_registry = HandlerRegistry(handlers)
    self.handler_registry.register_mappings()

    # Setup connection orchestrator
    self.connection_orchestrator = ConnectionOrchestrator(
        self.handler_registry)
    self.connection_orchestrator.initialize()

    logger.info("WebSocket handlers factory completed setup")

  def get_orchestrator(self):
    """Get the connection orchestrator."""
    return self.connection_orchestrator
