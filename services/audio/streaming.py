"""
Streaming audio processor for real-time audio handling.
Backward compatibility wrapper for modularized streaming components.
"""

# Import from modularized components
from .streaming import (
    StreamingConfig,
    StreamingProcessor,
    SilenceDetector,
    VoiceActivityDetector,
    AudioStreamService
)

# Re-export all classes for backward compatibility
__all__ = [
    'StreamingConfig',
    'StreamingProcessor',
    'SilenceDetector',
    'VoiceActivityDetector',
    'AudioStreamService'
]
