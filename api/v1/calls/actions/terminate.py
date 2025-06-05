"""
Endpoint for terminating calls
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from api.v1.schemas.request.call import CallTerminateRequest  
from api.v1.schemas.response.call import CallTerminateResponse
from services.call.management.supervisor import CallSupervisor
from core.security.auth.token import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

@router.post("/terminate", response_model=CallTerminateResponse)
async def terminate_call(
    request: CallTerminateRequest,
    current_user: Any = Depends(get_current_user)
) -> CallTerminateResponse:
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
        result = await supervisor.terminate_call(
            call_id=request.call_id,
            reason=request.reason
        )
        
        logger.info(f"Call {request.call_id} terminated successfully")
        
        return CallTerminateResponse(
            call_id=request.call_id,
            status="terminated",
            message="Call terminated successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to terminate call {request.call_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to terminate call: {str(e)}"
        )
