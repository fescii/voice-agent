"""
Call event handler for processing webhook events.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from data.db.ops.call import update_call_status
from data.redis.ops.session import update_call_session
from models.internal.callcontext import CallContext, CallStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


class CallEventHandler:
  """Handles call events from webhooks."""

  def __init__(self, active_calls: Dict[str, CallContext]):
    """Initialize with reference to active calls."""
    self.active_calls = active_calls

  async def handle_call_answered(
      self,
      call_context: CallContext,
      session
  ) -> bool:
    """Handle call answered event."""
    try:
      # Update call status
      success = await update_call_status(
          session=session,
          call_id=call_context.call_id,
          status=CallStatus.ANSWERED,
          answered_at=datetime.now(timezone.utc)
      )

      if success:
        # Update context
        call_context.status = CallStatus.ANSWERED
        call_context.start_time = datetime.now(timezone.utc)

        # Store updated context
        await update_call_session(
            call_id=call_context.call_id,
            session_data=call_context.model_dump(
                by_alias=True, exclude_none=True
            )
        )

        # Register as active call
        self.active_calls[call_context.call_id] = call_context

        logger.info(f"Call {call_context.call_id} answered and active")
        return True

      return False

    except Exception as e:
      logger.error(f"Failed to handle call answered: {e}")
      return False

  async def handle_call_hangup(
      self,
      call_context: CallContext,
      session
  ) -> bool:
    """Handle call hangup event."""
    try:
      # Update call status
      end_time = datetime.now(timezone.utc)
      success = await update_call_status(
          session=session,
          call_id=call_context.call_id,
          status=CallStatus.ENDED,
          ended_at=end_time
      )

      if success:
        # Calculate duration
        if call_context.start_time:
          duration = int((end_time - call_context.start_time).total_seconds())
          call_context.duration = duration

        # Update context
        call_context.status = CallStatus.ENDED
        call_context.end_time = end_time

        # Clean up
        await self._cleanup_call(call_context)

        logger.info(f"Call {call_context.call_id} ended successfully")
        return True

      return False

    except Exception as e:
      logger.error(f"Failed to handle call hangup: {e}")
      return False

  async def handle_call_failed(
      self,
      call_context: CallContext,
      session
  ) -> bool:
    """Handle call failed event."""
    try:
      # Update call status
      end_time = datetime.now(timezone.utc)
      success = await update_call_status(
          session=session,
          call_id=call_context.call_id,
          status=CallStatus.FAILED,
          ended_at=end_time
      )

      if success:
        # Update context
        call_context.status = CallStatus.FAILED
        call_context.end_time = end_time

        # Clean up
        await self._cleanup_call(call_context)

        logger.info(f"Call {call_context.call_id} marked as failed")
        return True

      return False

    except Exception as e:
      logger.error(f"Failed to handle call failure: {e}")
      return False

  async def _cleanup_call(self, call_context: CallContext) -> None:
    """Clean up call resources."""
    try:
      # Remove from active calls
      if call_context.call_id in self.active_calls:
        del self.active_calls[call_context.call_id]

      # Update session storage
      await update_call_session(
          call_id=call_context.call_id,
          session_data=call_context.dict()
      )

      logger.info(f"Cleaned up call {call_context.call_id}")

    except Exception as e:
      logger.error(f"Failed to cleanup call {call_context.call_id}: {e}")
