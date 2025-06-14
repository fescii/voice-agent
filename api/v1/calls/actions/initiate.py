"""
Endpoint for initiating outbound calls
"""
import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Any

from api.v1.schemas.request.call import CallInitiateRequest
from api.v1.schemas.response.call import CallInitiateResponse, CallStatus
from core.config.response import GenericResponse
from services.call.management.orchestrator import CallOrchestrator
from core.config.registry import config_registry
from api.dependencies.auth import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/initiate", response_model=GenericResponse[CallInitiateResponse])
async def initiate_outbound_call(
    request: CallInitiateRequest,
    current_user: Any = Depends(get_current_user)
) -> GenericResponse[CallInitiateResponse]:
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

    # Initialize call orchestrator with config check
    if not hasattr(config_registry, '_initialized') or not config_registry._initialized:
      config_registry.initialize()
    call_orchestrator = CallOrchestrator()

    # Use provided agent_id or fall back to default from config
    agent_id = request.agent_id or config_registry.agent.default_agent_id

    # Initiate outbound call
    session_id = await call_orchestrator.handle_outbound_call(
        phone_number=request.phone_number,
        agent_id=agent_id
    )

    if not session_id:
      return GenericResponse.error(
          message="Failed to initiate call - no available agents or configuration error",
          status_code=500
      )

    logger.info(f"Call initiated successfully with session ID: {session_id}")

    response_data = CallInitiateResponse(
        call_id=session_id,
        status=CallStatus.INITIATED,
        message="Call initiated successfully"
    )

    return GenericResponse.ok(
        data=response_data,
        status_code=200
    )

  except Exception as e:
    logger.error(f"Failed to initiate outbound call: {str(e)}")
    return GenericResponse.error(
        message="Failed to initiate call",
        details=str(e),
        status_code=500
    )
