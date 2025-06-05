"""
WebSocket Event Handlers

This module provides backward compatibility imports for WebSocket handlers.
The actual implementations have been modularized into specialized handler modules.
"""

# Import the main orchestrator and expose the key classes for backward compatibility
from .handlers.orchestrator import WebSocketHandlers, websocket_handlers

# Export the main handlers class and instance for backward compatibility
__all__ = [
    "WebSocketHandlers",
    "websocket_handlers"
]
