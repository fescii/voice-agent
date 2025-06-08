"""
Confirmation flow handler.
"""

from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ConfirmationHandler:
  """Handles confirmation flow processing."""

  def __init__(self):
    """Initialize confirmation handler."""
    pass

  async def handle(self, user_input: str, base_response, metadata: Dict[str, Any]):
    """Handle confirmation flow."""
    # Check for confirmation/rejection in user input
    is_confirmed = await self._detect_confirmation(user_input)

    if is_confirmed:
      enhanced_text = "Great! I'll proceed with that. " + base_response.text
      next_flow = "closing"
    else:
      enhanced_text = "I understand. Let me try a different approach. " + base_response.text
      next_flow = "gathering_info"

    from services.agent.core import AgentResponse
    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        metadata={**(base_response.metadata or {}), "flow": "confirming",
                  "confirmed": is_confirmed, "next_flow": next_flow}
    )

  async def _detect_confirmation(self, user_input: str) -> bool:
    """Detect confirmation or rejection in user input."""
    confirmation_words = ["yes", "yeah", "yep",
                          "correct", "right", "exactly", "proceed"]
    rejection_words = ["no", "nope", "wrong", "incorrect", "different"]

    user_lower = user_input.lower()

    has_confirmation = any(word in user_lower for word in confirmation_words)
    has_rejection = any(word in user_lower for word in rejection_words)

    # If both or neither, default to confirmation
    if has_confirmation and not has_rejection:
      return True
    elif has_rejection and not has_confirmation:
      return False
    else:
      return True  # Default to positive
