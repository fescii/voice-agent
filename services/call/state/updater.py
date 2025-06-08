"""
Call state update service
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from models.internal.callcontext import CallContext, CallStatus
from data.redis.ops.session.store import store_call_session
from data.redis.ops.session.retrieve import get_call_session
from data.redis.ops.session.delete import delete_call_session
from core.logging.setup import get_logger

logger = get_logger(__name__)


class CallStateUpdater:
  """Service for updating call states"""

  async def update_call_status(self, call_id: str, status: CallStatus,
                               additional_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Update the status of a call

    Args:
        call_id: The call identifier
        status: New call status
        additional_data: Additional context data

    Returns:
        True if update successful, False otherwise
    """
    try:
      # Get existing call session
      call_data = await get_call_session(call_id)

      if call_data:
        # Update the status in the data
        call_data["status"] = status.value
        call_data["last_updated"] = datetime.now(timezone.utc).isoformat()

        # Add any additional data
        if additional_data:
          call_data.get("context_data", {}).update(additional_data)

        # Store updated session
        return await store_call_session(call_id, call_data)
      else:
        logger.warning(f"Call session not found for {call_id}")
        return False

    except Exception as e:
      logger.error(f"Error updating call status for {call_id}: {e}")
      return False

  async def create_call_session(self, call_context: CallContext) -> bool:
    """
    Create a new call session

    Args:
        call_context: Call context data

    Returns:
        True if creation successful, False otherwise
    """
    try:
      # Convert CallContext to dict for storage
      session_data = call_context.dict()
      return await store_call_session(call_context.call_id, session_data)
    except Exception as e:
      logger.error(
          f"Error creating call session for {call_context.call_id}: {e}")
      return False

  async def end_call_session(self, call_id: str) -> bool:
    """
    End and cleanup a call session

    Args:
        call_id: The call identifier

    Returns:
        True if cleanup successful, False otherwise
    """
    try:
      # Update status to ended first
      await self.update_call_status(call_id, CallStatus.ENDED)

      # Delete from active sessions after a delay (for cleanup)
      # Note: In production, you might want to keep this for a short period
      # for debugging or move to a different storage
      return await delete_call_session(call_id)

    except Exception as e:
      logger.error(f"Error ending call session for {call_id}: {e}")
      return False
