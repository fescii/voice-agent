"""
Greeting flow handler.
"""

from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class GreetingHandler:
  """Handles greeting flow processing."""

  def __init__(self, agent_core):
    """Initialize greeting handler."""
    self.agent_core = agent_core

  async def handle(self, user_input: str, base_response, metadata: Dict[str, Any], turn_count: int):
    """Handle greeting flow."""
    # Check if this is the first interaction
    if turn_count == 0:
      greeting_text = await self._generate_personalized_greeting()
      # Import here to avoid circular imports
      from services.agent.core import AgentResponse
      return AgentResponse(
          text=greeting_text,
          confidence=1.0,
          metadata={"flow": "greeting", "personalized": True}
      )

    # Add welcoming elements to response
    enhanced_text = self._add_welcoming_tone(base_response.text)

    from services.agent.core import AgentResponse
    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**(base_response.metadata or {}), "flow": "greeting"}
    )

  async def _generate_personalized_greeting(self) -> str:
    """Generate a personalized greeting."""
    greetings = [
        f"Hello! I'm {self.agent_core.config.name}, and I'm here to help you today.",
        f"Hi there! This is {self.agent_core.config.name}. How can I assist you?",
        f"Good day! I'm {self.agent_core.config.name}, your AI assistant. What can I help you with?"
    ]

    # Could be enhanced with time-based greetings, caller history, etc.
    return greetings[0]

  def _add_welcoming_tone(self, text: str) -> str:
    """Add welcoming tone to response."""
    welcoming_phrases = ["I'm happy to help with that.",
                         "I'd be glad to assist you.", "Let me help you with that."]

    if not any(phrase in text.lower() for phrase in ["happy", "glad", "help"]):
      return f"{welcoming_phrases[0]} {text}"

    return text
