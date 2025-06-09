"""
Ringover streaming WebSocket endpoints.
Provides WebSocket routes for Ringover media server integration.
"""
from fastapi import APIRouter, WebSocket, Depends, status, HTTPException
from services.ringover.streaming.integrated import ringover_streamer_service
from core.logging.setup import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ringover", tags=["ringover-streaming"])


@router.get("/health")
async def streamer_health():
  """Health check endpoint for the Ringover streamer service."""
  health_status = ringover_streamer_service.get_health_status()

  if health_status["status"] != "healthy":
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Ringover streamer service is not healthy"
    )

  return health_status


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
