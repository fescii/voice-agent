"""
Call event handler for processing webhook events.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from data.db.ops.call import update_call_status
from data.redis.ops.session import update_call_session
from models.internal.callcontext import CallContext, CallStatus as ContextCallStatus
from data.db.models.calllog import CallStatus as DbCallStatus
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
          status=DbCallStatus.ANSWERED,
          answered_at=datetime.now(timezone.utc)
      )

      if success:
        # Update context
        call_context.status = ContextCallStatus.ANSWERED
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
          status=DbCallStatus.COMPLETED,
          ended_at=end_time
      )

      if success:
        # Calculate duration
        if call_context.start_time:
          duration = int((end_time - call_context.start_time).total_seconds())
          call_context.duration = duration

        # Update context
        call_context.status = ContextCallStatus.ENDED
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
          status=DbCallStatus.FAILED,
          ended_at=end_time
      )

      if success:
        # Update context
        call_context.status = ContextCallStatus.FAILED
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

  async def handle_event(self, webhook_event, session) -> bool:
    """
    Handle webhook events by routing to appropriate handlers.

    Args:
        webhook_event: The webhook event from Ringover
        session: Database session

    Returns:
        True if event was handled successfully
    """
    try:
      # Get or create call context
      call_context = await self._get_or_create_call_context(webhook_event)

      # Route to appropriate handler based on event type
      event_type = webhook_event.event_type.lower()

      if event_type in ['call_answered', 'answered']:
        return await self.handle_call_answered(call_context, session)
      elif event_type in ['call_hangup', 'hangup', 'ended']:
        return await self.handle_call_hangup(call_context, session)
      elif event_type in ['call_failed', 'failed']:
        return await self.handle_call_failed(call_context, session)
      else:
        logger.warning(f"Unhandled event type: {event_type}")
        return False

    except Exception as e:
      logger.error(f"Failed to handle event: {e}")
      return False

  async def _get_or_create_call_context(self, webhook_event) -> CallContext:
    """Get existing call context or create new one from webhook event."""
    # Check if we already have this call in active calls
    call_id = getattr(webhook_event, 'call_id', None)
    if call_id and call_id in self.active_calls:
      return self.active_calls[call_id]

    # Create new context from webhook event
    # This is a simplified version - you may need to adjust based on your webhook structure
    from models.internal.callcontext import CallDirection

    context = CallContext(
        call_id=call_id or str(webhook_event.get('id', '')),
        session_id=f"session_{call_id}",
        phone_number=getattr(webhook_event, 'phone_number', ''),
        agent_id=getattr(webhook_event, 'agent_id', 'default'),
        direction=CallDirection.INBOUND,
        status=ContextCallStatus.INITIATED,
        start_time=None,
        end_time=None,
        duration=None,
        ringover_call_id=getattr(webhook_event, 'ringover_call_id', None),
        websocket_id=None
    )

    return context
