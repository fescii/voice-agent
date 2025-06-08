"""
Call event handling functionality.
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable, Awaitable
from datetime import datetime

from core.logging.setup import get_logger
from ..models import WebhookEvent, WebhookEventType

logger = get_logger(__name__)


class CallStateTracker:
  """Tracks call states and transitions."""

  def __init__(self):
    self.call_states: Dict[str, Dict[str, Any]] = {}

  def update_call_state(self, call_id: str, status: str, timestamp: datetime, data: Dict[str, Any]):
    """Update call state."""
    if call_id not in self.call_states:
      self.call_states[call_id] = {}

    old_status = self.call_states[call_id].get("status")
    self.call_states[call_id]["status"] = status
    self.call_states[call_id][f"{status}_at"] = timestamp
    self.call_states[call_id]["data"] = data

    return old_status

  def get_call_state(self, call_id: str) -> Optional[Dict[str, Any]]:
    """Get call state by ID."""
    return self.call_states.get(call_id)


class CallEventHandler:
  """Handles call-specific webhook events."""

  def __init__(self):
    self.state_tracker = CallStateTracker()
    self.state_change_handlers: List[Callable[[
        str, str, str], Awaitable[None]]] = []

  def register_state_change_handler(self, handler: Callable[[str, str, str], Awaitable[None]]):
    """
    Register a handler for call state changes.

    Args:
        handler: Function that takes (call_id, old_state, new_state)
    """
    self.state_change_handlers.append(handler)
    logger.info("Registered call state change handler")

  async def handle_call_event(self, event: WebhookEvent):
    """
    Handle call-related webhook events.

    Args:
        event: Webhook event to handle
    """
    call_id = event.call_id
    old_state = self.state_tracker.get_call_state(call_id)
    old_status = old_state.get("status") if old_state else None

    # Process event based on type
    if event.event_type == WebhookEventType.CALL_INITIATED:
      await self._handle_call_initiated(event)
    elif event.event_type == WebhookEventType.CALL_RINGING:
      await self._handle_call_ringing(event)
    elif event.event_type == WebhookEventType.CALL_ANSWERED:
      await self._handle_call_answered(event)
    elif event.event_type == WebhookEventType.CALL_ENDED:
      await self._handle_call_ended(event)
    elif event.event_type == WebhookEventType.CALL_FAILED:
      await self._handle_call_failed(event)

    # Notify state change handlers
    new_state = self.state_tracker.get_call_state(call_id)
    new_status = new_state.get("status") if new_state else None

    if old_status != new_status and new_status:
      await self._notify_state_change(call_id, old_status or "unknown", new_status)

  async def _handle_call_initiated(self, event: WebhookEvent):
    """Handle call initiated event."""
    self.state_tracker.update_call_state(
        event.call_id, "initiated", event.timestamp, event.data
    )
    logger.info(f"Call {event.call_id} initiated")

  async def _handle_call_ringing(self, event: WebhookEvent):
    """Handle call ringing event."""
    self.state_tracker.update_call_state(
        event.call_id, "ringing", event.timestamp, event.data
    )
    logger.info(f"Call {event.call_id} ringing")

  async def _handle_call_answered(self, event: WebhookEvent):
    """Handle call answered event."""
    self.state_tracker.update_call_state(
        event.call_id, "answered", event.timestamp, event.data
    )
    logger.info(f"Call {event.call_id} answered")

  async def _handle_call_ended(self, event: WebhookEvent):
    """Handle call ended event."""
    # Add duration to data if available
    data = event.data.copy()
    if "duration" in event.data:
      data["duration"] = event.data["duration"]

    self.state_tracker.update_call_state(
        event.call_id, "ended", event.timestamp, data
    )
    logger.info(f"Call {event.call_id} ended")

  async def _handle_call_failed(self, event: WebhookEvent):
    """Handle call failed event."""
    # Add failure reason to data if available
    data = event.data.copy()
    if "reason" in event.data:
      data["failure_reason"] = event.data["reason"]

    self.state_tracker.update_call_state(
        event.call_id, "failed", event.timestamp, data
    )
    logger.info(f"Call {event.call_id} failed")

  async def _notify_state_change(self, call_id: str, old_state: str, new_state: str):
    """Notify registered handlers of state change."""
    tasks = [handler(call_id, old_state, new_state)
             for handler in self.state_change_handlers]
    try:
      await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
      logger.error(f"Error notifying state change handlers: {e}")

  def get_call_state(self, call_id: str) -> Optional[Dict[str, Any]]:
    """Get current call state."""
    return self.state_tracker.get_call_state(call_id)
