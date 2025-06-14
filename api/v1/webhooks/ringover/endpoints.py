"""
Individual webhook endpoints for each Ringover event type
"""
from fastapi import APIRouter, Request, HTTPException, status, Header
from typing import Optional

from models.external.ringover.webhook import RingoverWebhookEvent
from api.v1.webhooks.ringover.event import get_orchestrator, _verify_webhook_signature, _route_webhook_event
from core.config.registry import config_registry
from core.logging.setup import get_logger
from core.config.response import GenericResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/calls/ringing", response_model=GenericResponse[dict])
async def handle_calls_ringing(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle calls ringing webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "call_ringing")


@router.post("/calls/answered", response_model=GenericResponse[dict])
async def handle_calls_answered(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle calls answered webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "call_answered")


@router.post("/calls/ended", response_model=GenericResponse[dict])
async def handle_calls_ended(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle calls ended webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "call_ended")


@router.post("/calls/missed", response_model=GenericResponse[dict])
async def handle_missed_calls(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle missed calls webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "missed_call")


@router.post("/voicemail", response_model=GenericResponse[dict])
async def handle_voicemail(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle voicemail webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "voicemail")


@router.post("/sms/received", response_model=GenericResponse[dict])
async def handle_sms_received(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle SMS received webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "sms_received")


@router.post("/sms/sent", response_model=GenericResponse[dict])
async def handle_sms_sent(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle SMS sent webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "sms_sent")


@router.post("/aftercall/work", response_model=GenericResponse[dict])
async def handle_after_call_work(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle after-call work webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "after_call_work")


@router.post("/fax/received", response_model=GenericResponse[dict])
async def handle_fax_received(
    request: Request,
    x_ringover_signature: Optional[str] = Header(None)
) -> GenericResponse[dict]:
  """Handle fax received webhook events"""
  return await _handle_webhook_event(request, x_ringover_signature, "fax_received")


async def _handle_webhook_event(
    request: Request,
    x_ringover_signature: Optional[str],
    event_type: str
) -> GenericResponse[dict]:
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
      return GenericResponse.error("Invalid webhook signature", status.HTTP_401_UNAUTHORIZED)

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

    return GenericResponse.ok({"status": "success", "message": f"{event_type} event processed"})

  except Exception as e:
    logger.error(f"Failed to process {event_type} webhook event: {str(e)}")
    return GenericResponse.error(f"Failed to process {event_type} webhook: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
