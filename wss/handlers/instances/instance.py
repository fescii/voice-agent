"""
Global WebSocket handlers instance.
"""

from ..factory.main import HandlersFactory
from core.logging.setup import get_logger

logger = get_logger(__name__)

# Create and initialize global handlers
_handlers_factory = HandlersFactory()
_handlers_factory.create()

# Global connection orchestrator instance
websocket_handlers = _handlers_factory.get_orchestrator()

logger.info("Global WebSocket handlers instance created")
