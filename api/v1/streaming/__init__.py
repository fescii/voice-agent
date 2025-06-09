"""
API endpoints for real-time streaming services.
"""
from fastapi import APIRouter
from .audio import router as audio_router
from .ringover import router as ringover_router

router = APIRouter(prefix="/streaming", tags=["streaming"])

# Include sub-routers
router.include_router(audio_router)
router.include_router(ringover_router)

__all__ = ["router", "audio_router", "ringover_router"]
