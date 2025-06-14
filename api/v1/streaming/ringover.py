"""
Ringover streaming WebSocket endpoints.
Provides WebSocket routes for Ringover media server integration.
"""
from fastapi import APIRouter, WebSocket, Depends, status, HTTPException
from services.ringover.streaming.integrated import ringover_streamer_service
from core.logging.setup import get_logger
from core.config.response import GenericResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/ringover", tags=["ringover-streaming"])


@router.get("/health", response_model=GenericResponse[dict])
async def streamer_health():
  """Health check endpoint for the Ringover streamer service."""
  try:
    health_status = ringover_streamer_service.get_health_status()

    if health_status["status"] != "healthy":
      return GenericResponse.error("Ringover streamer service is not healthy", status.HTTP_503_SERVICE_UNAVAILABLE)

    return GenericResponse.ok(health_status)
  except Exception as e:
    return GenericResponse.error(f"Health check failed: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.websocket("/ws")
async def ringover_websocket(websocket: WebSocket):
  """
  WebSocket endpoint for Ringover media server connections.

  This endpoint receives:
  - RTP audio data from Ringover media servers
  - Control commands for audio processing

  It can send:
  - Audio responses for voicebot functionality
  - Status messages and confirmations
  """
  await ringover_streamer_service.handle_websocket_connection(websocket)
