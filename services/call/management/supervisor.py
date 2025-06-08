"""
Call supervisor service for managing active calls using modular components.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from data.db.ops.call import get_call_by_ringover_id
from data.redis.ops.session import get_call_session
from models.external.ringover.webhook import RingoverWebhookEvent
from models.internal.callcontext import CallContext
from core.logging.setup import get_logger

from .supervisor import CallEventHandler, CallLifecycleManager, CallOperationsManager

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
          f"Handling call event: {event_type} for {ringover_call_id}")

      # Get call context
      call_log = await get_call_by_ringover_id(session, ringover_call_id)
      if not call_log:
        logger.warning(
            f"No call log found for Ringover call {ringover_call_id}")
        return False

      call_context = await self._get_call_context(call_log.call_id)
      if not call_context:
        logger.warning(f"No call context found for {call_log.call_id}")
        return False

      # Handle specific events using event handler
      if event_type == "call_answered":
        return await self.event_handler.handle_call_answered(call_context, session)
      elif event_type == "call_hangup":
        return await self.event_handler.handle_call_hangup(call_context, session)
      elif event_type == "call_failed":
        return await self.event_handler.handle_call_failed(call_context, session)
      else:
        logger.info(f"Unhandled event type: {event_type}")
        return True

    except Exception as e:
      logger.error(f"Failed to handle call event: {e}")
      return False

  async def _get_call_context(self, call_id: str) -> Optional[CallContext]:
    """Get call context from active calls or session storage."""
    # Check active calls first
    if call_id in self._active_calls:
      return self._active_calls[call_id]

    # Try to load from session storage
    try:
      session_data = await get_call_session(call_id)
      if session_data:
        call_context = CallContext.parse_obj(session_data)
        return call_context
    except Exception as e:
      logger.error(f"Failed to get call context for {call_id}: {e}")

    return None

  # Delegate methods to appropriate managers
  async def start_call(self, call_id: str, agent_id: str, phone_number: str, websocket_id: Optional[str] = None) -> Optional[CallContext]:
    """Start a new call."""
    return await self.lifecycle_manager.start_call(call_id, agent_id, phone_number, websocket_id)

  async def end_call(self, call_id: str) -> bool:
    """End a call."""
    return await self.lifecycle_manager.end_call(call_id)

  async def transfer_call(self, call_id: str, target_number: str) -> bool:
    """Transfer a call."""
    return await self.operations_manager.transfer_call(call_id, target_number)

  async def send_dtmf(self, call_id: str, tone: str) -> bool:
    """Send DTMF tone."""
    return await self.operations_manager.send_dtmf(call_id, tone)

  def get_active_calls(self) -> List[CallContext]:
    """Get all active calls."""
    return self.lifecycle_manager.get_active_calls()

  def get_call_count(self) -> int:
    """Get count of active calls."""
    return self.lifecycle_manager.get_call_count()

  async def _handle_call_answered(
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
          status="answered",
          answered_at=datetime.now(timezone.utc)
      )

      if success:
        # Update context
        call_context.status = CallStatus.ANSWERED
        call_context.start_time = datetime.now(timezone.utc)

        # Store updated context
        await update_call_session(
            call_id=call_context.call_id,
            session_data=call_context.dict()
        )

        # Register as active call
        self._active_calls[call_context.call_id] = call_context

        self.logger.info(f"Call {call_context.call_id} answered and active")
        return True

      return False

    except Exception as e:
      self.logger.error(f"Failed to handle call answered: {e}")
      return False

  async def _handle_call_hangup(
      self,
      call_context: CallContext,
      session
  ) -> bool:
    """Handle call hangup event."""
    try:
      # Calculate duration
      duration = None
      if call_context.start_time:
        duration = (datetime.now(timezone.utc) -
                    call_context.start_time).total_seconds()

      # Update call status
      success = await update_call_status(
          session=session,
          call_id=call_context.call_id,
          status="completed",
          ended_at=datetime.now(timezone.utc),
          duration_seconds=duration
      )

      if success:
        # Clean up
        await self._cleanup_call(call_context, session)
        self.logger.info(f"Call {call_context.call_id} completed")
        return True

      return False

    except Exception as e:
      self.logger.error(f"Failed to handle call hangup: {e}")
      return False

  async def _handle_call_failed(
      self,
      call_context: CallContext,
      session
  ) -> bool:
    """Handle call failed event."""
    try:
      # Update call status
      success = await update_call_status(
          session=session,
          call_id=call_context.call_id,
          status="failed",
          ended_at=datetime.now(timezone.utc)
      )

      if success:
        # Clean up
        await self._cleanup_call(call_context, session)
        self.logger.info(f"Call {call_context.call_id} failed")
        return True

      return False

    except Exception as e:
      self.logger.error(f"Failed to handle call failed: {e}")
      return False

  async def _cleanup_call(self, call_context: CallContext, session) -> None:
    """Clean up call resources."""
    try:
      # Remove from active calls
      self._active_calls.pop(call_context.call_id, None)

      # Delete session data
      await delete_call_session(call_context.call_id)

      # Update agent call count
      await update_agent_call_count(
          session,
          call_context.agent_id,
          increment=-1
      )

    except Exception as e:
      self.logger.error(f"Failed to cleanup call {call_context.call_id}: {e}")

  async def _get_call_context(self, call_id: str) -> Optional[CallContext]:
    """Get call context from Redis or memory."""
    try:
      # Try memory first
      if call_id in self._active_calls:
        return self._active_calls[call_id]

      # Try Redis
      session_data = await get_call_session(call_id)
      if session_data:
        return CallContext(**session_data)

      return None

    except Exception as e:
      self.logger.error(f"Failed to get call context for {call_id}: {e}")
      return None

  def get_active_calls(self) -> List[CallContext]:
    """Get list of active calls."""
    return list(self._active_calls.values())

  def get_call_count(self) -> int:
    """Get total number of active calls."""
    return len(self._active_calls)

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
      self._active_calls[call_id] = call_context

      # Store session data
      await store_call_session(call_id, call_context.dict())

      self.logger.info(f"Started call {call_id} with agent {agent_id}")
      return call_context

    except Exception as e:
      self.logger.error(f"Failed to start call {call_id}: {e}")
      return None

  async def end_call(self, call_id: str) -> bool:
    """
    End an active call.

    Args:
        call_id: Call identifier to end

    Returns:
        True if call was ended successfully
    """
    try:
      call_context = self._active_calls.get(call_id)
      if not call_context:
        self.logger.warning(f"No active call found for {call_id}")
        return False

      # Update status
      call_context.status = CallStatus.ENDED
      call_context.end_time = datetime.now(timezone.utc)

      if call_context.start_time:
        call_context.duration = int(
            (call_context.end_time - call_context.start_time).total_seconds())

      # Clean up resources
      # Session will be handled separately
      await self._cleanup_call(call_context, None)

      self.logger.info(f"Ended call {call_id}")
      return True

    except Exception as e:
      self.logger.error(f"Failed to end call {call_id}: {e}")
      return False

  async def transfer_call(self, call_id: str, target_number: str) -> bool:
    """
    Transfer a call to another number.

    Args:
        call_id: Call identifier to transfer
        target_number: Target phone number

    Returns:
        True if transfer was initiated successfully
    """
    try:
      call_context = self._active_calls.get(call_id)
      if not call_context:
        self.logger.warning(f"No active call found for transfer: {call_id}")
        return False

      # TODO: Implement actual transfer logic with Ringover API
      # For now, just log and return success
      self.logger.info(
          f"Transfer initiated for call {call_id} to {target_number}")

      # Update call context
      call_context.metadata["transfer_target"] = target_number
      call_context.metadata["transfer_initiated_at"] = datetime.utcnow(
      ).isoformat()

      return True

    except Exception as e:
      self.logger.error(f"Failed to transfer call {call_id}: {e}")
      return False

  async def send_dtmf(self, call_id: str, tone: str) -> bool:
    """
    Send DTMF tone to a call.

    Args:
        call_id: Call identifier
        tone: DTMF tone to send

    Returns:
        True if DTMF was sent successfully
    """
    try:
      call_context = self._active_calls.get(call_id)
      if not call_context:
        self.logger.warning(f"No active call found for DTMF: {call_id}")
        return False

      # TODO: Implement actual DTMF sending with Ringover API
      # For now, just log and return success
      self.logger.info(f"DTMF tone '{tone}' sent to call {call_id}")

      # Track DTMF in metadata
      if "dtmf_tones" not in call_context.metadata:
        call_context.metadata["dtmf_tones"] = []
      call_context.metadata["dtmf_tones"].append({
          "tone": tone,
          "timestamp": datetime.now(timezone.utc).isoformat()
      })

      return True

    except Exception as e:
      self.logger.error(f"Failed to send DTMF to call {call_id}: {e}")
      return False
