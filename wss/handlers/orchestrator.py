"""
WebSocket handlers orchestrator.
Imports from the new modular structure for backward compatibility.
"""

# Import from the new modular structure
from .instances import websocket_handlers

# Maintain backward compatibility
WebSocketHandlers = type(websocket_handlers)

__all__ = ["websocket_handlers", "WebSocketHandlers"]
