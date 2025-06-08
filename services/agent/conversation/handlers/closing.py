"""
Closing flow handler.
"""

from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ClosingHandler:
  """Handles closing flow processing."""

  def __init__(self):
    """Initialize closing handler."""
    pass

  async def handle(self, user_input: str, base_response, metadata: Dict[str, Any]):
    """Handle closing flow."""
    # Add closing elements
    closing_text = base_response.text

    if not any(phrase in closing_text.lower() for phrase in ["thank", "goodbye", "bye"]):
      closing_text += " Thank you for calling. Is there anything else I can help you with?"

    from services.agent.core import AgentResponse
    return AgentResponse(
        text=closing_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**(base_response.metadata or {}), "flow": "closing"}
    )
