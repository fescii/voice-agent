"""
Text-to-Speech service module.
"""

from .elevenlabs import ElevenLabsService

# Create service aliases for compatibility
ElevenLabsTTSService = ElevenLabsService

__all__ = [
    "ElevenLabsService",
    "ElevenLabsTTSService"
]
