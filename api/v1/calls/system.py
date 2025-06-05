"""
Call system status endpoint with startup context integration.
"""
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from core.startup.context import get_service
from services.call.manager import CallManager

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=Dict[str, Any])
async def get_call_system_info(
    telephony_service=Depends(lambda req: get_service(req, "telephony"))
):
  """
  Get call system information with integrated telephony service status.

  Requires the telephony service to be available in the startup context.
  """
  call_manager = CallManager()

  return {
      "active_calls": await call_manager.get_active_call_count(),
      "telephony_provider": telephony_service.get("provider", "unknown"),
      "telephony_status": telephony_service.get("status", "unknown"),
      "api_available": telephony_service.get("api_available", False)
  }
