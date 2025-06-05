"""
Speech-to-Text service module.
"""

from .whisper import WhisperService

# Create service aliases for compatibility
WhisperSTTService = WhisperService

__all__ = [
    "WhisperService",
    "WhisperSTTService"
]
