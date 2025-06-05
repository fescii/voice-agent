"""
Endpoint for initiating outbound calls
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any

from api.v1.schemas.request.call import CallInitiateRequest
from api.v1.schemas.response.call import CallInitiateResponse
from services.call.initiation.outbound import OutboundCallService
from core.security.auth.token import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/initiate", response_model=CallInitiateResponse)
async def initiate_outbound_call(
    request: CallInitiateRequest,
    current_user: Any = Depends(get_current_user)
) -> CallInitiateResponse:
  """
  Initiate an outbound call through Ringover

  Args:
      request: Call initiation request data
      current_user: Authenticated user

  Returns:
      Call initiation response with call ID and status

  Raises:
      HTTPException: If call initiation fails
  """
  try:
    logger.info(
        f"Initiating outbound call to {request.phone_number} for user {current_user}")

    outbound_service = OutboundCallService()
    call_result = await outbound_service.initiate_call(
        phone_number=request.phone_number,
        agent_id=request.agent_id,
        caller_id=request.caller_id,
        context=request.context
    )

    logger.info(f"Call initiated successfully with ID: {call_result.call_id}")

    return CallInitiateResponse(
        call_id=call_result.call_id,
        status=call_result.status,
        message="Call initiated successfully"
    )

  except Exception as e:
    logger.error(f"Failed to initiate outbound call: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to initiate call: {str(e)}"
    )
