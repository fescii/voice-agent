"""
Endpoint for getting call status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from api.v1.schemas.response.call import CallStatusResponse
from services.call.state.tracker import CallStateTracker
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/{call_id}/status", response_model=CallStatusResponse)
async def get_call_status(
    call_id: str,
    current_user: Any = Depends(get_current_user)
) -> CallStatusResponse:
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

    tracker = CallStateTracker()
    call_state = await tracker.get_call_state(call_id)

    if not call_state:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail=f"Call {call_id} not found"
      )

    logger.info(f"Retrieved status for call {call_id}: {call_state.status}")

    return CallStatusResponse(
        call_id=call_id,
        status=call_state.status,
        agent_id=call_state.agent_id,
        phone_number=call_state.phone_number,
        start_time=call_state.start_time,
        duration=call_state.duration,
        metadata=call_state.metadata
    )

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get status for call {call_id}: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to get call status: {str(e)}"
    )
