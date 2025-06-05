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
from core.config.app import ConfigurationManager
from core.config.providers.telephony import RingoverConfig, TelephonyProvider
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Global orchestrator instance
_orchestrator: Optional[CallOrchestrator] = None


def get_orchestrator() -> CallOrchestrator:
  """Get or create call orchestrator instance."""
  global _orchestrator
  if _orchestrator is None:
    config_manager = ConfigurationManager()
    system_config = config_manager.get_configuration()
    _orchestrator = CallOrchestrator(system_config)
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
    config_manager = ConfigurationManager()
    system_config = config_manager.get_configuration()
    webhook_secret = getattr(
        system_config.telephony_config, 'webhook_secret', None)

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
  Route webhook event to call orchestrator for handling

  Args:
      event: Parsed webhook event
  """
  orchestrator = get_orchestrator()

  logger.info(
      f"Routing webhook event: {event.event_type} for call {event.call_id}")

  if event.event_type == "call_initiated":
    # Handle outbound call initiated
    logger.info(f"Call {event.call_id} initiated")

  elif event.event_type == "call_answered":
    # Update call status and handle answer
    logger.info(f"Call {event.call_id} answered")

  elif event.event_type == "call_ended":
    # End call session
    session_ids = [sid for sid, session in orchestrator.active_sessions.items()
                   if session.call_info.call_id == event.call_id]
    for session_id in session_ids:
      await orchestrator.end_call(session_id)
    logger.info(f"Call {event.call_id} ended")

  elif event.event_type == "call_failed":
    # Handle call failure
    session_ids = [sid for sid, session in orchestrator.active_sessions.items()
                   if session.call_info.call_id == event.call_id]
    for session_id in session_ids:
      await orchestrator.end_call(session_id)
    logger.warning(f"Call {event.call_id} failed")

  elif event.event_type == "incoming_call":
    # Handle incoming call - try to extract call details from event data
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

  else:
    logger.warning(f"Unhandled webhook event type: {event.event_type}")
