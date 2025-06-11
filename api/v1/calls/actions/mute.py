"""
Endpoint for muting a call
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from api.v1.schemas.request.call import CallMuteRequest
from api.v1.schemas.response.call import CallMuteResponse
from services.call.state.manager import CallStateManager, CallState
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/mute", response_model=CallMuteResponse)
async def mute_call(
    request: CallMuteRequest,
    current_user: Any = Depends(get_current_user)
) -> CallMuteResponse:
  """
  Mute or unmute an active call

  Args:
      request: Call mute request data
      current_user: Authenticated user

  Returns:
      Call mute response

  Raises:
      HTTPException: If call mute operation fails
  """
  try:
    logger.info(
        f"Setting mute status for call {request.call_id} to {request.muted} for user {current_user}")

    manager = CallStateManager()

    # Get current state first to validate call exists
    current_state_info = await manager.get_state(request.call_id)
    if not current_state_info:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Call {request.call_id} not found"
      )

    # Update state based on mute request
    new_state = CallState.MUTED if request.muted else CallState.CONNECTED
    await manager.update_state(
        call_id=request.call_id,
        new_state=new_state,
        metadata={"muted": request.muted}
    )

    logger.info(f"Call {request.call_id} mute status set to {request.muted}")

    return CallMuteResponse(
        call_id=request.call_id,
        muted=request.muted,
        status="success",
        message=f"Call {'muted' if request.muted else 'unmuted'} successfully"
    )

  except Exception as e:
    logger.error(
        f"Failed to set mute status for call {request.call_id}: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to set mute status: {str(e)}"
    )
