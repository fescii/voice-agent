"""
Call event handlers for Ringover webhooks.
"""
from typing import Optional

from models.external.ringover.webhook import RingoverWebhookEvent
from services.call.management.orchestrator import CallOrchestrator
from services.ringover import CallInfo, CallDirection, CallStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def handle_call_ringing(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle call ringing event"""
  if not event.call_id:
    logger.warning("Received call ringing event without call_id")
    return

  logger.info(f"Call {event.call_id} is ringing")
  # Extract call details from event data
  from_number = event.data.get("from_number", "unknown")
  to_number = event.data.get("to_number", "unknown")
  direction = event.data.get("direction", "unknown")

  if direction == "inbound":
    call_info = CallInfo(
        call_id=event.call_id,
        phone_number=from_number,
        direction=CallDirection.INBOUND,
        status=CallStatus.RINGING,
        metadata=event.data
    )
    session_id = await orchestrator.handle_inbound_call(call_info)
    if session_id:
      logger.info(f"Incoming call handled, session: {session_id}")


async def handle_call_answered(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle call answered event"""
  logger.info(f"Call {event.call_id} answered")
  # Update call status in active sessions
  active_sessions = await orchestrator.get_active_sessions()
  for session in active_sessions:
    if session.call_info.call_id == event.call_id:
      session.call_info.status = CallStatus.ANSWERED
      logger.info(
          f"Updated call status to answered for session {session.call_context.session_id}")


async def handle_call_ended(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle call ended event"""
  active_sessions = await orchestrator.get_active_sessions()
  session_ids = [session.call_context.session_id for session in active_sessions
                 if session.call_info.call_id == event.call_id]
  for session_id in session_ids:
    await orchestrator.end_call(session_id)
  logger.info(f"Call {event.call_id} ended")


async def handle_call_failed_or_missed(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle call failure or missed call event"""
  active_sessions = await orchestrator.get_active_sessions()
  session_ids = [session.call_context.session_id for session in active_sessions
                 if session.call_info.call_id == event.call_id]
  for session_id in session_ids:
    await orchestrator.end_call(session_id)
  logger.warning(f"Call {event.call_id} failed or missed: {event.event_type}")


async def handle_incoming_call(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle incoming call event"""
  if not event.call_id:
    logger.warning("Received incoming call event without call_id")
    return

  call_info = CallInfo(
      call_id=event.call_id,
      phone_number=event.data.get("caller_number", "unknown"),
      direction=CallDirection.INBOUND,
      status=CallStatus.RINGING,
      metadata=event.data
  )
  session_id = await orchestrator.handle_inbound_call(call_info)
  if session_id:
    logger.info(f"Incoming call handled, session: {session_id}")
  else:
    logger.warning(f"Failed to handle incoming call {event.call_id}")
