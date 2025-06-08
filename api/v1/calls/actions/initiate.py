"""
Endpoint for initiating outbound calls
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any

from api.v1.schemas.request.call import CallInitiateRequest
from api.v1.schemas.response.call import CallInitiateResponse, CallStatus
from services.call.management.orchestrator import CallOrchestrator
from core.config.registry import config_registry
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

    # Initialize call orchestrator
    call_orchestrator = CallOrchestrator()

    # Initiate outbound call
    session_id = await call_orchestrator.initiate_outbound_call(
        to_number=request.phone_number,
        agent_id=request.agent_id,
        metadata=request.context or {}
    )

    if not session_id:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Failed to initiate call - no available agents or configuration error"
      )

    logger.info(f"Call initiated successfully with session ID: {session_id}")

    return CallInitiateResponse(
        call_id=session_id,
        status=CallStatus.INITIATED,
        message="Call initiated successfully"
    )

  except Exception as e:
    logger.error(f"Failed to initiate outbound call: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Failed to initiate call: {str(e)}"
    )
