"""
Endpoint for transferring calls
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from api.v1.schemas.request.call import CallTransferRequest
from api.v1.schemas.response.call import CallTransferResponse, CallStatus
from core.config.response import GenericResponse
from services.call.management.supervisor.main import CallSupervisor
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/transfer", response_model=GenericResponse[CallTransferResponse])
async def transfer_call(
    request: CallTransferRequest,
    current_user: Any = Depends(get_current_user)
) -> GenericResponse[CallTransferResponse]:
  """
  Transfer an active call to another number or agent

  Args:
      request: Call transfer request data
      current_user: Authenticated user

  Returns:
      Call transfer response

  Raises:
      HTTPException: If call transfer fails
  """
  try:
    logger.info(
        f"Transferring call {request.call_id} to {request.target_number} for user {current_user}")

    supervisor = CallSupervisor()
    result = await supervisor.transfer_call(
        call_id=request.call_id,
        target_number=request.target_number
    )

    logger.info(f"Call {request.call_id} transferred successfully")

    transfer_response = CallTransferResponse(
        call_id=request.call_id,
        target_number=request.target_number,
        status=CallStatus.TRANSFERRED,
        message="Call transferred successfully"
    )

    return GenericResponse.ok(transfer_response)

  except Exception as e:
    logger.error(f"Failed to transfer call {request.call_id}: {str(e)}")
    return GenericResponse.error(f"Failed to transfer call: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
