"""
Main router for /calls endpoints
"""
from fastapi import APIRouter

from api.v1.calls.actions.initiate import router as initiate_router
from api.v1.calls.actions.terminate import router as terminate_router
from api.v1.calls.actions.transfer import router as transfer_router
from api.v1.calls.actions.mute import router as mute_router
from api.v1.calls.status import router as status_router

# Create the main calls router
router = APIRouter(prefix="/calls", tags=["calls"])

# Include action routers
router.include_router(initiate_router, prefix="/actions")
router.include_router(terminate_router, prefix="/actions")
router.include_router(transfer_router, prefix="/actions")
router.include_router(mute_router, prefix="/actions")

# Include status router
router.include_router(status_router)
