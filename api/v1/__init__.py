"""
API Version 1 main router
"""
from fastapi import APIRouter

from api.v1.calls.route import router as calls_router
from api.v1.agents.route import router as agents_router
from api.v1.webhooks.ringover.route import router as ringover_webhooks_router
from api.v1.streaming import router as streaming_router
from api.v1.admin import router as admin_router

# Create the main v1 router
router = APIRouter()

# Include all sub-routers
router.include_router(calls_router)
router.include_router(agents_router)
router.include_router(ringover_webhooks_router,
                      prefix="/webhooks/ringover", tags=["webhooks"])
router.include_router(streaming_router)
router.include_router(admin_router)
