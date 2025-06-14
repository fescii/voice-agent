"""
Endpoint for terminating calls
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from api.v1.schemas.request.call import CallTerminateRequest
from api.v1.schemas.response.call import CallTerminateResponse, CallStatus
from core.config.response import GenericResponse
from services.call.management.supervisor import CallSupervisor
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/terminate", response_model=GenericResponse[CallTerminateResponse])
async def terminate_call(
    request: CallTerminateRequest,
    current_user: Any = Depends(get_current_user)
) -> GenericResponse[CallTerminateResponse]:
  """
  Terminate an active call

  Args:
      request: Call termination request data
      current_user: Authenticated user

  Returns:
      Call termination response

  Raises:
      HTTPException: If call termination fails
  """
  try:
    logger.info(f"Terminating call {request.call_id} for user {current_user}")

    supervisor = CallSupervisor()
    result = await supervisor.end_call(call_id=request.call_id)

    logger.info(f"Call {request.call_id} terminated successfully")

    response_data = CallTerminateResponse(
        call_id=request.call_id,
        status=CallStatus.TERMINATED,
        message="Call terminated successfully"
    )

    return GenericResponse.ok(
        data=response_data,
        status_code=200
    )

  except Exception as e:
    logger.error(f"Failed to terminate call {request.call_id}: {str(e)}")
    return GenericResponse.error(
        message="Failed to terminate call",
        details=str(e),
        status_code=500
    )
