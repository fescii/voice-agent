"""
Individual webhook endpoints for each Ringover event type
"""
from fastapi import APIRouter, Request, HTTPException, status, Header
from typing import Optional

from models.external.ringover.webhook import RingoverWebhookEvent
from api.v1.webhooks.ringover.event import get_orchestrator, _verify_webhook_signature, _route_webhook_event
from core.config.registry import config_registry
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/calls/ringing")
async def handle_calls_ringing(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle calls ringing webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "call_ringing")


@router.post("/calls/answered")
async def handle_calls_answered(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle calls answered webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "call_answered")


@router.post("/calls/ended")
async def handle_calls_ended(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle calls ended webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "call_ended")


@router.post("/calls/missed")
async def handle_missed_calls(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle missed calls webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "missed_call")


@router.post("/voicemail")
async def handle_voicemail(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle voicemail webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "voicemail")


@router.post("/sms/received")
async def handle_sms_received(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle SMS received webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "sms_received")


@router.post("/sms/sent")
async def handle_sms_sent(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle SMS sent webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "sms_sent")


@router.post("/aftercall/work")
async def handle_after_call_work(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle after-call work webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "after_call_work")


@router.post("/fax/received")
async def handle_fax_received(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> dict:
  """Handle fax received webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "fax_received")


async def _handle_webhook_event(
    request: Request,
    x_ringover_signature: Optional[str],
    event_type: str
) -> dict:
  """
  Common webhook event handler

  Args:
      request: FastAPI request object
      x_ringover_signature: HMAC signature for verification
      event_type: Type of webhook event

  Returns:
      Acknowledgment response
  """
  try:
    # Get raw body for signature verification
    body = await request.body()

    # Get webhook secret from centralized config
    webhook_secret = config_registry.ringover.webhook_secret

    # Verify webhook signature if secret is configured
    if webhook_secret and not _verify_webhook_signature(body, x_ringover_signature, webhook_secret):
      logger.warning(f"Invalid webhook signature for {event_type}")
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid webhook signature"
      )

    # Parse webhook payload
    payload = await request.json()

    # Override event type with the specific endpoint event type
    payload['event_type'] = event_type

    webhook_event = RingoverWebhookEvent(**payload)

    logger.info(
        f"Received {event_type} webhook event for call {webhook_event.call_id}")

    # Route event to appropriate handler
    await _route_webhook_event(webhook_event)

    logger.info(f"Successfully processed {event_type} webhook event")

    return {"status": "success", "message": f"{event_type} event processed"}

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to process {event_type} webhook event: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to process {event_type} webhook: {str(e)}"
    )
