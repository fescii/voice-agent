"""
Handles incoming Ringover webhook events
"""
from fastapi import APIRouter, Request, HTTPException, status, Header
from typing import Optional
import hmac
import hashlib

from models.external.ringover.webhook import RingoverWebhookEvent
from services.call.management.orchestrator import CallOrchestrator
from services.ringover import CallInfo, CallDirection, CallStatus
from core.config.registry import config_registry
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Global orchestrator instance
_orchestrator: Optional[CallOrchestrator] = None


def get_orchestrator() -> CallOrchestrator:
  """Get or create call orchestrator instance."""
  global _orchestrator
  if _orchestrator is None:
    # Ensure config registry is initialized before creating orchestrator
    if not hasattr(config_registry, '_initialized') or not config_registry._initialized:
      config_registry.initialize()
    _orchestrator = CallOrchestrator()
  return _orchestrator


@router.post("/event")
async def handle_ringover_event(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """
  Handle incoming Ringover webhook events

  Args:
      request: FastAPI request object containing the webhook payload
      x_ringover_signature: HMAC signature for webhook verification

  Returns:
      Acknowledgment response

  Raises:
      HTTPException: If webhook verification fails or processing error occurs
  """
  try:
    # Get raw body for signature verification
    body = await request.body()

    # Get system configuration for webhook verification
    webhook_secret = config_registry.ringover.webhook_secret

    # Verify webhook signature if secret is configured
    if webhook_secret and not _verify_webhook_signature(body, x_ringover_signature, webhook_secret):
      logger.warning("Invalid webhook signature received")
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid webhook signature"
      )

    # Parse webhook payload
    payload = await request.json()
    webhook_event = RingoverWebhookEvent(**payload)

    logger.info(
        f"Received Ringover webhook event: {webhook_event.event_type} for call {webhook_event.call_id}")

    # Route event to appropriate handler
    await _route_webhook_event(webhook_event)

    logger.info(
        f"Successfully processed webhook event: {webhook_event.event_type}")

    return {"status": "success", "message": "Event processed"}

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to process webhook event: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to process webhook: {str(e)}"
    )


def _verify_webhook_signature(body: bytes, signature: Optional[str], secret: str) -> bool:
  """
  Verify HMAC signature of webhook payload

  Args:
      body: Raw webhook payload
      signature: Received signature
      secret: Webhook secret for verification

  Returns:
      True if signature is valid, False otherwise
  """
  if not signature or not secret:
    return False

  try:
    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
      signature = signature[7:]

    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

  except Exception as e:
    logger.error(f"Error verifying webhook signature: {str(e)}")
    return False


async def _route_webhook_event(event: RingoverWebhookEvent) -> None:
  """
  Route webhook event to appropriate handler based on event type

  Args:
      event: Parsed webhook event
  """
  orchestrator = get_orchestrator()

  logger.info(
      f"Routing webhook event: {event.event_type} for call {event.call_id}")

  # Call-related events
  if event.event_type in ["call_ringing", "call_initiated"]:
    await _handle_call_ringing(event, orchestrator)

  elif event.event_type == "call_answered":
    await _handle_call_answered(event, orchestrator)

  elif event.event_type == "call_ended":
    await _handle_call_ended(event, orchestrator)

  elif event.event_type in ["call_failed", "missed_call"]:
    await _handle_call_failed_or_missed(event, orchestrator)

  elif event.event_type == "incoming_call":
    await _handle_incoming_call(event, orchestrator)

  # Voicemail events
  elif event.event_type == "voicemail":
    await _handle_voicemail(event)

  # SMS events
  elif event.event_type == "sms_received":
    await _handle_sms_received(event)

  elif event.event_type == "sms_sent":
    await _handle_sms_sent(event)

  # After-call work events
  elif event.event_type == "after_call_work":
    await _handle_after_call_work(event)

  # Fax events
  elif event.event_type == "fax_received":
    await _handle_fax_received(event)

  # WebSocket events (for audio streaming)
  elif event.event_type == "websocket_connected":
    await _handle_websocket_connected(event, orchestrator)

  elif event.event_type == "websocket_disconnected":
    await _handle_websocket_disconnected(event, orchestrator)

  else:
    logger.warning(f"Unhandled webhook event type: {event.event_type}")


async def _handle_call_ringing(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
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


async def _handle_call_answered(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle call answered event"""
  logger.info(f"Call {event.call_id} answered")
  # Update call status in active sessions
  active_sessions = await orchestrator.get_active_sessions()
  for session in active_sessions:
    if session.call_info.call_id == event.call_id:
      session.call_info.status = CallStatus.ANSWERED
      logger.info(
          f"Updated call status to answered for session {session.call_context.session_id}")


async def _handle_call_ended(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle call ended event"""
  active_sessions = await orchestrator.get_active_sessions()
  session_ids = [session.call_context.session_id for session in active_sessions
                 if session.call_info.call_id == event.call_id]
  for session_id in session_ids:
    await orchestrator.end_call(session_id)
  logger.info(f"Call {event.call_id} ended")


async def _handle_call_failed_or_missed(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle call failure or missed call event"""
  active_sessions = await orchestrator.get_active_sessions()
  session_ids = [session.call_context.session_id for session in active_sessions
                 if session.call_info.call_id == event.call_id]
  for session_id in session_ids:
    await orchestrator.end_call(session_id)
  logger.warning(f"Call {event.call_id} failed or missed: {event.event_type}")


async def _handle_incoming_call(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
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


async def _handle_voicemail(event: RingoverWebhookEvent) -> None:
  """Handle voicemail event"""
  logger.info(
      f"Voicemail received from {event.data.get('caller_number', 'unknown')}")
  # TODO: Implement voicemail processing logic
  # Could involve transcription, notification, storage, etc.


async def _handle_sms_received(event: RingoverWebhookEvent) -> None:
  """Handle SMS received event"""
  from_number = event.data.get('from_number', 'unknown')
  message_content = event.data.get('message_content', '')
  logger.info(f"SMS received from {from_number}: {message_content[:50]}...")
  # TODO: Implement SMS processing logic
  # Could involve auto-responses, logging, integration with chat systems, etc.


async def _handle_sms_sent(event: RingoverWebhookEvent) -> None:
  """Handle SMS sent event"""
  to_number = event.data.get('to_number', 'unknown')
  logger.info(f"SMS sent to {to_number}")
  # TODO: Implement SMS sent tracking
  # Could involve delivery confirmation, logging, etc.


async def _handle_after_call_work(event: RingoverWebhookEvent) -> None:
  """Handle after-call work event"""
  agent_id = event.data.get('agent_id', 'unknown')
  logger.info(f"After-call work event for agent {agent_id}")
  # TODO: Implement after-call work processing
  # Could involve call summary generation, CRM updates, etc.


async def _handle_fax_received(event: RingoverWebhookEvent) -> None:
  """Handle fax received event"""
  from_number = event.data.get('from_number', 'unknown')
  logger.info(f"Fax received from {from_number}")
  # TODO: Implement fax processing logic
  # Could involve OCR, document processing, notifications, etc.


async def _handle_websocket_connected(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle WebSocket audio connection established"""
  logger.info(f"WebSocket connected for call {event.call_id}")
  # TODO: Set up audio streaming handlers


async def _handle_websocket_disconnected(event: RingoverWebhookEvent, orchestrator: CallOrchestrator) -> None:
  """Handle WebSocket audio connection disconnected"""
  logger.info(f"WebSocket disconnected for call {event.call_id}")
  # TODO: Clean up audio streaming handlers
