"""
Main router for Ringover webhooks
"""
from fastapi import APIRouter

from api.v1.webhooks.ringover.event import router as event_router
from api.v1.webhooks.ringover.test import router as test_router
from api.v1.webhooks.ringover.endpoints import router as endpoints_router

# Create the main Ringover webhooks router
router = APIRouter()

# Include event router (main endpoint)
router.include_router(event_router)

# Include individual endpoints for each event type
router.include_router(endpoints_router)

# Include test router for webhook verification
router.include_router(test_router)
