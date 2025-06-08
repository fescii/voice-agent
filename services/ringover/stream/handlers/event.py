"""
Event handlers for WebSocket events.
"""
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from ..models import EventHandler

logger = get_logger(__name__)


class EventMessageHandler:
  """Handler for event messages."""

  def __init__(self):
    """Initialize event message handler."""
    self.event_handler: Optional[EventHandler] = None

  def set_event_handler(self, handler: EventHandler):
    """
    Set the event processing handler.

    Args:
        handler: Function to process incoming events
    """
    self.event_handler = handler

  async def handle_event_message(self, call_id: str, data: Dict[str, Any]):
    """
    Handle incoming event message.

    Args:
        call_id: ID of the call
        data: Event message data
    """
    if self.event_handler:
      event_data = {
          "call_id": call_id,
          "event_type": data.get("event"),
          "data": data.get("data", {})
      }
      await self.event_handler(event_data)
