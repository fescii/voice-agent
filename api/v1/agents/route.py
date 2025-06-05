"""
Main router for /agents endpoints
"""
from fastapi import APIRouter

from api.v1.agents.config.route import router as config_router
from api.v1.agents.status import router as status_router

# Create the main agents router
router = APIRouter(prefix="/agents", tags=["agents"])

# Include sub-routers
router.include_router(config_router, prefix="/config")
router.include_router(status_router)
