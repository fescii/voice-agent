"""
Call system status endpoint with startup context integration.
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from core.startup.context import get_service
from services.call.manager import CallManager
from core.config.response import GenericResponse

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=GenericResponse[Dict[str, Any]])
async def get_call_system_info(
    telephony_service=Depends(lambda req: get_service(req, "telephony"))
):
  """
  Get call system information with integrated telephony service status.

  Requires the telephony service to be available in the startup context.
  """
  try:
    call_manager = CallManager()

    data = {
        "active_calls": await call_manager.get_active_call_count(),
        "telephony_provider": telephony_service.get("provider", "unknown"),
        "telephony_status": telephony_service.get("status", "unknown"),
        "api_available": telephony_service.get("api_available", False)
    }

    return GenericResponse.ok(data)
  except Exception as e:
    return GenericResponse.error(f"Failed to get call system info: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
