"""
Main router for Ringover webhooks
"""
from fastapi import APIRouter

from api.v1.webhooks.ringover.event import router as event_router

# Create the main Ringover webhooks router
router = APIRouter()

# Include event router
router.include_router(event_router)
