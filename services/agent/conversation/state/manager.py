"""
Flow state management and transitions.
"""

from typing import Dict, Any, List
from ..flow.definitions import ConversationFlow, ConversationTurn
from core.logging.setup import get_logger

logger = get_logger(__name__)


class FlowStateManager:
  """Manages conversation flow state transitions."""

  def __init__(self):
    """Initialize flow state manager."""
    self.current_flow = ConversationFlow.GREETING
    self.conversation_turns: List[ConversationTurn] = []
    self.error_count = 0
    self.max_errors = 3

  async def determine_next_flow(self, user_input: str, response) -> ConversationFlow:
    """Determine the next conversation flow state."""
    try:
      current_turn_count = len(self.conversation_turns)

      # Flow transition logic
      if self.current_flow == ConversationFlow.GREETING:
        if current_turn_count >= 1:
          return ConversationFlow.GATHERING_INFO

      elif self.current_flow == ConversationFlow.GATHERING_INFO:
        if await self._has_sufficient_information():
          return ConversationFlow.PROCESSING_REQUEST

      elif self.current_flow == ConversationFlow.PROCESSING_REQUEST:
        if response.action or response.confidence > 0.8:
          return ConversationFlow.PROVIDING_SOLUTION

      elif self.current_flow == ConversationFlow.PROVIDING_SOLUTION:
        return ConversationFlow.CONFIRMING

      elif self.current_flow == ConversationFlow.CONFIRMING:
        # Handled in confirmation handler
        pass

      elif self.current_flow == ConversationFlow.CLOSING:
        # Check if user wants to continue
        continue_indicators = ["more", "another", "also", "else"]
        if any(indicator in user_input.lower() for indicator in continue_indicators):
          return ConversationFlow.GATHERING_INFO

      return self.current_flow

    except Exception as e:
      logger.error(f"Error determining next flow: {str(e)}")
      return self.current_flow

  def set_flow(self, flow: ConversationFlow):
    """Set conversation flow."""
    logger.info(
        f"Conversation flow changed: {self.current_flow.value} -> {flow.value}")
    self.current_flow = flow

  def get_flow(self) -> ConversationFlow:
    """Get current conversation flow."""
    return self.current_flow

  def increment_error_count(self):
    """Increment error count and check for error handling flow."""
    self.error_count += 1
    if self.error_count >= self.max_errors:
      self.current_flow = ConversationFlow.ERROR_HANDLING

  def reset_error_count(self):
    """Reset error count on successful processing."""
    self.error_count = 0

  async def _has_sufficient_information(self) -> bool:
    """Check if we have sufficient information to proceed."""
    # This would typically check conversation context
    # For now, simplified implementation
    return len(self.conversation_turns) >= 2
