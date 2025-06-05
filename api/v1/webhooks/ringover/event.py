"""
Handles incoming Ringover webhook events
"""
from fastapi import APIRouter, Request, HTTPException, status, Header
from typing import Optional
import hmac
import hashlib

from models.external.ringover.webhook import RingoverWebhookEvent
from services.call.management.supervisor import CallSupervisor
from services.call.state.updater import CallStateUpdater
from core.config.providers.ringover import RingoverConfig
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

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
        
        # Verify webhook signature
        ringover_config = RingoverConfig()
        if not _verify_webhook_signature(body, x_ringover_signature, ringover_config.webhook_secret):
            logger.warning("Invalid webhook signature received")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse webhook payload
        payload = await request.json()
        webhook_event = RingoverWebhookEvent(**payload)
        
        logger.info(f"Received Ringover webhook event: {webhook_event.event_type} for call {webhook_event.call_id}")
        
        # Route event to appropriate handler
        await _route_webhook_event(webhook_event)
        
        logger.info(f"Successfully processed webhook event: {webhook_event.event_type}")
        
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
    Route webhook event to appropriate service handler
    
    Args:
        event: Parsed webhook event
    """
    supervisor = CallSupervisor()
    state_updater = CallStateUpdater()
    
    if event.event_type == "call_initiated":
        await supervisor.handle_call_initiated(event)
        
    elif event.event_type == "call_answered":
        await supervisor.handle_call_answered(event)
        await state_updater.update_call_status(event.call_id, "answered")
        
    elif event.event_type == "call_ended":
        await supervisor.handle_call_ended(event)
        await state_updater.update_call_status(event.call_id, "ended")
        
    elif event.event_type == "call_failed":
        await supervisor.handle_call_failed(event)
        await state_updater.update_call_status(event.call_id, "failed")
        
    elif event.event_type == "incoming_call":
        await supervisor.handle_incoming_call(event)
        
    else:
        logger.warning(f"Unhandled webhook event type: {event.event_type}")
