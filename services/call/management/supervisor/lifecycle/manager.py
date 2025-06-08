"""
Call lifecycle manager for handling call creation and termination.
"""
from typing import Optional, Dict
import uuid
from datetime import datetime, timezone

from data.redis.ops.session import store_call_session, delete_call_session
from models.internal.callcontext import CallContext, CallDirection, CallStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


class CallLifecycleManager:
  """Manages call lifecycle operations."""

  def __init__(self, active_calls: Dict[str, CallContext]):
    """Initialize with reference to active calls."""
    self.active_calls = active_calls

  async def start_call(
      self,
      call_id: str,
      agent_id: str,
      phone_number: str,
      websocket_id: Optional[str] = None
  ) -> Optional[CallContext]:
    """
    Start a new call and create call context.

    Args:
        call_id: Unique call identifier
        agent_id: Agent handling the call
        phone_number: Phone number for the call
        websocket_id: WebSocket connection ID

    Returns:
        Created CallContext or None if failed
    """
    try:
      # Create call context
      call_context = CallContext(
          call_id=call_id,
          session_id=str(uuid.uuid4()),
          phone_number=phone_number,
          agent_id=agent_id,
          direction=CallDirection.OUTBOUND,
          status=CallStatus.INITIATED,
          start_time=datetime.now(timezone.utc),
          end_time=None,
          duration=None,
          ringover_call_id=None,
          websocket_id=websocket_id
      )

      # Store in active calls
      self.active_calls[call_id] = call_context

      # Store session data
      await store_call_session(call_id, call_context.dict())

      logger.info(f"Started call {call_id} with agent {agent_id}")
      return call_context

    except Exception as e:
      logger.error(f"Failed to start call {call_id}: {e}")
      return None

  async def end_call(self, call_id: str) -> bool:
    """
    End a call and clean up resources.

    Args:
        call_id: Call identifier

    Returns:
        True if call ended successfully
    """
    try:
      call_context = self.active_calls.get(call_id)
      if not call_context:
        logger.warning(f"Call {call_id} not found in active calls")
        return False

      # Update call context
      call_context.status = CallStatus.ENDED
      call_context.end_time = datetime.now(timezone.utc)

      if call_context.start_time:
        duration = call_context.end_time - call_context.start_time
        call_context.duration = int(duration.total_seconds())

      # Remove from active calls
      del self.active_calls[call_id]

      # Clean up session data
      await delete_call_session(call_id)

      logger.info(f"Ended call {call_id}")
      return True

    except Exception as e:
      logger.error(f"Failed to end call {call_id}: {e}")
      return False

  def get_active_calls(self) -> list[CallContext]:
    """Get list of all active calls."""
    return list(self.active_calls.values())

  def get_call_count(self) -> int:
    """Get count of active calls."""
    return len(self.active_calls)
