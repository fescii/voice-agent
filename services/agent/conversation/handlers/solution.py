"""
Solution providing flow handler.
"""

from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class SolutionHandler:
  """Handles solution providing flow."""

  def __init__(self):
    """Initialize solution handler."""
    pass

  async def handle(self, user_input: str, base_response, metadata: Dict[str, Any]):
    """Handle solution providing flow."""
    # Add solution framing
    solution_intro = "Here's what I can do to help: "
    enhanced_text = f"{solution_intro}{base_response.text}"

    # Add follow-up question
    follow_up = " Does this solution work for you?"
    enhanced_text += follow_up

    from services.agent.core import AgentResponse
    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**(base_response.metadata or {}),
                  "flow": "providing_solution"}
    )
