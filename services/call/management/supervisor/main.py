"""
Main call supervisor class that coordinates all supervisor components.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from data.db.ops.call import get_call_by_ringover_id
from data.redis.ops.session import get_call_session
from models.external.ringover.webhook import RingoverWebhookEvent
from models.internal.callcontext import CallContext
from core.logging.setup import get_logger

from .events.handler import CallEventHandler
from .lifecycle.manager import CallLifecycleManager
from .operations.manager import CallOperationsManager

logger = get_logger(__name__)


class CallSupervisor:
  """
  Service for supervising and managing active calls.
  Uses modular components for event handling, lifecycle management, and operations.
  """

  def __init__(self):
    self._active_calls: Dict[str, CallContext] = {}

    # Initialize modular components
    self.event_handler = CallEventHandler(self._active_calls)
    self.lifecycle_manager = CallLifecycleManager(self._active_calls)
    self.operations_manager = CallOperationsManager(self._active_calls)

  async def handle_call_event(
      self,
      webhook_event: RingoverWebhookEvent,
      session
  ) -> bool:
    """
    Handle call events from Ringover webhooks.

    Args:
        webhook_event: Webhook event data
        session: Database session

    Returns:
        True if event was handled successfully
    """
    try:
      event_type = webhook_event.event_type
      ringover_call_id = webhook_event.call_id

      logger.info(
          f"Handling call event: {event_type} for call {ringover_call_id}")

      # Use modular event handler
      return await self.event_handler.handle_event(webhook_event, session)

    except Exception as e:
      logger.error(f"Error handling call event: {e}")
      return False

  async def get_active_calls(self) -> Dict[str, CallContext]:
    """Get all active calls."""
    return self._active_calls.copy()

  async def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a specific call."""
    return await self.operations_manager.get_call_status(call_id)

  async def cleanup_inactive_calls(self):
    """Clean up inactive calls."""
    await self.lifecycle_manager.cleanup_inactive_calls()

  async def get_call_metrics(self) -> Dict[str, Any]:
    """Get call metrics."""
    return await self.operations_manager.get_call_metrics()

  async def update_call_context(self, call_id: str, context_updates: Dict[str, Any]):
    """Update call context."""
    await self.operations_manager.update_call_context(call_id, context_updates)

  async def end_call(self, call_id: str):
    """End a call."""
    await self.lifecycle_manager.end_call(call_id)

  async def pause_call(self, call_id: str):
    """Pause a call."""
    await self.operations_manager.pause_call(call_id)

  async def resume_call(self, call_id: str):
    """Resume a call."""
    await self.operations_manager.resume_call(call_id)
