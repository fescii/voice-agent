"""
API endpoints for real-time streaming services.
"""
from .audio import router as audio_router

__all__ = [
    "audio_router"
]
