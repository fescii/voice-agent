"""
Backward compatibility module for Ringover streaming components.

The actual implementation has been moved to the streaming/ subfolder.
This module is maintained for backward compatibility.
"""

# Re-export classes from the new implementation
from services.ringover.streaming.service import RingoverStreamingService
from services.ringover.streaming.handler import RingoverStreamHandler

# Re-export ConversationContext for backward compatibility
from services.llm.prompt.builder import ConversationContext

__all__ = [
    "RingoverStreamingService",
    "RingoverStreamHandler",
    "ConversationContext"
]
