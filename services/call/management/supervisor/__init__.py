"""
Call supervisor module for managing active calls.
"""

from .events.handler import CallEventHandler
from .lifecycle.manager import CallLifecycleManager
from .operations.manager import CallOperationsManager

# For backward compatibility, define CallSupervisor here
from typing import Dict, Any, List, Optional
from models.internal.callcontext import CallContext
from models.external.ringover.webhook import RingoverWebhookEvent
from core.logging.setup import get_logger

logger = get_logger(__name__)


class CallSupervisor:
  """Simplified CallSupervisor for backward compatibility."""

  def __init__(self):
    self._active_calls: Dict[str, CallContext] = {}
    self.event_handler = CallEventHandler(self._active_calls)
    self.lifecycle_manager = CallLifecycleManager(self._active_calls)
    self.operations_manager = CallOperationsManager(self._active_calls)

  async def handle_call_event(self, webhook_event: RingoverWebhookEvent, session) -> bool:
    """Handle call events from Ringover webhooks."""
    try:
      event_type = webhook_event.event_type
      logger.info(f"Handling call event: {event_type}")
      return True
    except Exception as e:
      logger.error(f"Error handling call event: {e}")
      return False

  def get_active_calls(self) -> List[CallContext]:
    """Get all active calls."""
    return self.lifecycle_manager.get_active_calls()

  def get_call_count(self) -> int:
    """Get count of active calls."""
    return self.lifecycle_manager.get_call_count()

  async def start_call(self, call_id: str, agent_id: str, phone_number: str, websocket_id: Optional[str] = None) -> Optional[CallContext]:
    """Start a call."""
    return await self.lifecycle_manager.start_call(call_id, agent_id, phone_number, websocket_id)

  async def end_call(self, call_id: str) -> bool:
    """End a call."""
    return await self.lifecycle_manager.end_call(call_id)


__all__ = [
    'CallEventHandler',
    'CallLifecycleManager',
    'CallOperationsManager',
    'CallSupervisor'
]
