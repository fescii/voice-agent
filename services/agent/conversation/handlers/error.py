"""
Error handling flow handler.
"""

from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ErrorHandler:
  """Handles error flow processing."""

  def __init__(self):
    """Initialize error handler."""
    pass

  async def handle(self, user_input: str, base_response, metadata: Dict[str, Any], error_count: int):
    """Handle error flow."""
    error_responses = [
        "I apologize for the confusion. Let me transfer you to a human agent who can better assist you.",
        "I'm having trouble understanding your request. Would you like to speak with a human representative?",
        "Let me connect you with one of our specialists who can help you better."
    ]

    error_text = error_responses[min(
        error_count - 1, len(error_responses) - 1)]

    from services.agent.core import AgentResponse
    return AgentResponse(
        text=error_text,
        confidence=0.2,
        action="transfer",
        metadata={"flow": "error_handling", "error_count": error_count}
    )
