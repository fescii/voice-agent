"""
Test endpoint for webhook verification
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/test")
async def test_webhook(request: Request) -> Dict[str, Any]:
  """
  Test endpoint to verify webhook connectivity and payload structure

  This endpoint can be used to test webhook delivery from Ringover
  without processing the events through the main event handler.
  """
  try:
    # Get the raw payload
    body = await request.body()
    payload = await request.json()

    # Log the webhook test
    logger.info("Received webhook test payload")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Payload: {payload}")

    # Return the payload for verification
    return {
        "status": "success",
        "message": "Webhook test received successfully",
        "received_payload": payload,
        "headers": dict(request.headers),
        "body_size": len(body)
    }

  except Exception as e:
    logger.error(f"Error processing webhook test: {str(e)}")
    raise HTTPException(
        status_code=500,
        detail=f"Error processing webhook test: {str(e)}"
    )
