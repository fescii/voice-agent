"""
Real-time audio streaming endpoints for call integration.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from typing import Dict, Any, Optional
import asyncio
import json

from services.call.management.orchestrator import CallOrchestrator
from services.ringover.stream import RingoverWebSocketStreamer, AudioFrame
from core.config import SystemConfiguration, ConfigurationManager
from core.config.providers.telephony import TelephonyProvider
from core.config.providers.telephony import RingoverConfig as TelephonyRingoverConfig
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Global orchestrator and active streamers
_orchestrator: Optional[CallOrchestrator] = None
_active_streamers: Dict[str, RingoverWebSocketStreamer] = {}


def get_orchestrator() -> CallOrchestrator:
  """Get or create call orchestrator instance."""
  global _orchestrator
  if _orchestrator is None:
    config_manager = ConfigurationManager()
    system_config = config_manager.get_configuration()
    _orchestrator = CallOrchestrator(system_config)
  return _orchestrator


@router.websocket("/audio/{session_id}")
async def audio_streaming_websocket(
    websocket: WebSocket,
    session_id: str
):
  """
  WebSocket endpoint for real-time audio streaming.

  This endpoint connects to the Ringover audio stream for a specific call session
  and provides bidirectional audio streaming capabilities.

  Args:
      websocket: WebSocket connection from client
      session_id: Call session identifier
  """
  try:
    # Accept WebSocket connection
    await websocket.accept()
    logger.info(
        f"Audio streaming WebSocket connected for session: {session_id}")

    # Get orchestrator and verify session exists
    orchestrator = get_orchestrator()
    session = orchestrator.active_sessions.get(session_id)

    if not session:
      await websocket.send_text(json.dumps({
          "error": "Session not found",
          "code": "SESSION_NOT_FOUND"
      }))
      await websocket.close(code=1008, reason="Session not found")
      return

    # Initialize Ringover WebSocket streamer
    orchestrator = get_orchestrator()

    # Get Ringover config from system config
    if isinstance(orchestrator.system_config.telephony_config, TelephonyRingoverConfig):
      ringover_config = orchestrator.system_config.telephony_config
    else:
      # Create a default RingoverConfig if needed
      from core.config.providers.telephony import RingoverConfig
      # The config will load values from environment variables via the config system
      ringover_config = RingoverConfig(
          provider=TelephonyProvider.RINGOVER,
          api_key=""  # Will be loaded from environment via config system
      )

    ringover_streamer = RingoverWebSocketStreamer(ringover_config)

    # Set up handlers
    ringover_streamer.set_audio_handler(
        lambda frame: _handle_ringover_audio(session_id, frame, websocket)
    )

    # Store streamer reference
    _active_streamers[session_id] = ringover_streamer

    # Connect to Ringover audio stream
    # Get auth token from standalone config for streaming
    from core.config.providers.ringover import RingoverConfig as StandaloneRingoverConfig
    standalone_config = StandaloneRingoverConfig()

    success = await ringover_streamer.connect(
        call_id=session.call_info.call_id,
        auth_token=standalone_config.streamer_auth_token or "dummy_token"
    )
    if not success:
      await websocket.send_text(json.dumps({
          "error": "Failed to connect to Ringover audio stream",
          "code": "RINGOVER_CONNECTION_FAILED"
      }))
      await websocket.close(code=1011, reason="Upstream connection failed")
      return

    # Send connection success message
    await websocket.send_text(json.dumps({
        "status": "connected",
        "session_id": session_id,
        "call_id": session.call_info.call_id
    }))

    # Handle incoming WebSocket messages
    while True:
      try:
        # Receive audio data from client
        data = await websocket.receive_bytes()

        # Create audio frame and send to Ringover
        audio_frame = AudioFrame(
            call_id=session.call_info.call_id,
            audio_data=data,
            sample_rate=16000,  # Default rate
            channels=1
        )

        await ringover_streamer.send_audio(
            call_id=session.call_info.call_id,
            audio_data=data
        )

      except WebSocketDisconnect:
        logger.info(f"Client disconnected from audio stream: {session_id}")
        break
      except Exception as e:
        logger.error(f"Error in audio streaming loop: {e}")
        await websocket.send_text(json.dumps({
            "error": str(e),
            "code": "STREAMING_ERROR"
        }))
        break

  except Exception as e:
    logger.error(
        f"Failed to establish audio streaming for session {session_id}: {e}")
    try:
      await websocket.send_text(json.dumps({
          "error": str(e),
          "code": "CONNECTION_ERROR"
      }))
    except:
      pass
  finally:
    # Cleanup
    await _cleanup_audio_stream(session_id)


async def _handle_ringover_audio(session_id: str, audio_frame: AudioFrame, websocket: WebSocket):
  """
  Handle audio received from Ringover and forward to client.

  Args:
      session_id: Call session identifier
      audio_frame: Audio data from Ringover
      websocket: Client WebSocket connection
  """
  try:
    # Send audio data to client
    await websocket.send_bytes(audio_frame.audio_data)
  except Exception as e:
    logger.error(
        f"Failed to forward audio to client for session {session_id}: {e}")


async def _handle_ringover_disconnection(session_id: str):
  """
  Handle Ringover audio stream disconnection.

  Args:
      session_id: Call session identifier
  """
  logger.warning(
      f"Ringover audio stream disconnected for session: {session_id}")
  await _cleanup_audio_stream(session_id)


async def _cleanup_audio_stream(session_id: str):
  """
  Cleanup audio streaming resources.

  Args:
      session_id: Call session identifier
  """
  try:
    # Disconnect Ringover streamer if exists
    streamer = _active_streamers.pop(session_id, None)
    if streamer:
      await streamer.disconnect(session_id)

    logger.info(f"Audio streaming cleanup completed for session: {session_id}")
  except Exception as e:
    logger.error(f"Error during audio streaming cleanup: {e}")


@router.post("/{session_id}/control")
async def audio_control(session_id: str, action: Dict[str, Any]):
  """
  Control audio streaming settings.

  Args:
      session_id: Call session identifier
      action: Control action (mute, unmute, adjust_volume, etc.)

  Returns:
      Control action result
  """
  try:
    orchestrator = get_orchestrator()
    session = orchestrator.active_sessions.get(session_id)

    if not session:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Session not found"
      )

    streamer = _active_streamers.get(session_id)
    if not streamer:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="No active audio stream for this session"
      )

    action_type = action.get("type")

    if action_type == "mute":
      await streamer.mute(session_id)
      return {"status": "muted"}

    elif action_type == "unmute":
      await streamer.unmute(session_id)
      return {"status": "unmuted"}

    elif action_type == "adjust_volume":
      volume = action.get("volume", 1.0)
      await streamer.set_volume(session_id, volume)
      return {"status": "volume_adjusted", "volume": volume}

    else:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail=f"Unknown action type: {action_type}"
      )

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Audio control error for session {session_id}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )


@router.get("/{session_id}/status")
async def audio_stream_status(session_id: str):
  """
  Get audio streaming status for a session.

  Args:
      session_id: Call session identifier

  Returns:
      Audio streaming status information
  """
  try:
    orchestrator = get_orchestrator()
    session = orchestrator.active_sessions.get(session_id)

    if not session:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Session not found"
      )

    streamer = _active_streamers.get(session_id)

    return {
        "session_id": session_id,
        "call_id": session.call_info.call_id,
        "streaming_active": streamer is not None,
        "is_muted": streamer.is_muted if streamer else False,
        "connection_status": "connected" if streamer and streamer.is_connected else "disconnected"
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(
        f"Error getting audio stream status for session {session_id}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )
