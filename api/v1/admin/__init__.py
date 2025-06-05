"""
Admin API endpoints.
"""
from fastapi import APIRouter

from api.v1.admin.database import router as database_router

# Create admin router
router = APIRouter(prefix="/admin", tags=["admin"])

# Include all sub-routers
router.include_router(database_router)
