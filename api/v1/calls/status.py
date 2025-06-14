"""
Endpoint for getting call status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from api.v1.schemas.response.call import CallStatusResponse, CallStatus
from services.call.state.manager import CallStateManager, CallState
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger
from core.config.response import GenericResponse

logger = get_logger(__name__)
router = APIRouter()


def map_call_state_to_status(call_state: CallState) -> CallStatus:
  """Map CallState to CallStatus."""
  mapping = {
      CallState.INITIALIZING: CallStatus.INITIATED,
      CallState.RINGING: CallStatus.RINGING,
      CallState.CONNECTED: CallStatus.ANSWERED,
      CallState.ON_HOLD: CallStatus.IN_PROGRESS,
      CallState.MUTED: CallStatus.IN_PROGRESS,
      CallState.TRANSFERRING: CallStatus.TRANSFERRED,
      CallState.RECORDING: CallStatus.IN_PROGRESS,
      CallState.ENDING: CallStatus.ENDED,
      CallState.ENDED: CallStatus.ENDED,
      CallState.FAILED: CallStatus.FAILED
  }
  return mapping.get(call_state, CallStatus.INITIATED)


@router.get("/{call_id}/status", response_model=GenericResponse[CallStatusResponse])
async def get_call_status(
    call_id: str,
    current_user: Any = Depends(get_current_user)
) -> GenericResponse[CallStatusResponse]:
  """
  Get the current status of a call

  Args:
      call_id: The unique identifier of the call
      current_user: Authenticated user

  Returns:
      Current call status information

  Raises:
      HTTPException: If call not found or access denied
  """
  try:
    logger.info(f"Getting status for call {call_id} for user {current_user}")

    manager = CallStateManager()
    call_state = await manager.get_state(call_id)

    if not call_state:
      return GenericResponse.error(f"Call {call_id} not found", status.HTTP_404_NOT_FOUND)

    logger.info(f"Retrieved status for call {call_id}: {call_state.state}")

    # Map CallState to CallStatus and handle missing fields
    call_status_response = CallStatusResponse(
        call_id=call_id,
        status=map_call_state_to_status(call_state.state),
        agent_id=call_state.agent_id or "unknown",  # Handle None
        phone_number="",  # Not available in CallStateInfo
        start_time=call_state.timestamp,  # Use timestamp as start_time
        duration=None,  # Not available in CallStateInfo
        metadata=call_state.metadata
    )

    return GenericResponse.ok(call_status_response)

  except Exception as e:
    logger.error(f"Failed to get status for call {call_id}: {str(e)}")
    return GenericResponse.error(f"Failed to get call status: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
