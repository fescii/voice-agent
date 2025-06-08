"""
Processing flow handler.
"""

from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ProcessingHandler:
  """Handles request processing flow."""

  def __init__(self):
    """Initialize processing handler."""
    pass

  async def handle(self, user_input: str, base_response, metadata: Dict[str, Any]):
    """Handle request processing flow."""
    # Add processing indicators
    processing_prefixes = [
        "Let me look into that for you.",
        "I'm checking on that now.",
        "Let me find the best solution for you."
    ]

    # Use confidence to select appropriate prefix
    if base_response.confidence > 0.8:
      prefix = processing_prefixes[0]
    elif base_response.confidence > 0.5:
      prefix = processing_prefixes[1]
    else:
      prefix = processing_prefixes[2]

    enhanced_text = f"{prefix} {base_response.text}"

    from services.agent.core import AgentResponse
    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**(base_response.metadata or {}),
                  "flow": "processing_request"}
    )
