"""
Main authentication router that combines all auth endpoints.
"""
from fastapi import APIRouter

from .login import router as login_router
from .register import router as register_router
from .admin import router as admin_router

# Create main auth router
router = APIRouter()

# Include all auth sub-routers
router.include_router(login_router)
router.include_router(register_router)
router.include_router(admin_router)
