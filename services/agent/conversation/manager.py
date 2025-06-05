"""
Core conversation manager.
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable
import time

from core.logging.setup import get_logger
from services.agent.core import AgentCore, AgentResponse, AgentState
from services.agent.conversation.flow import ConversationFlow
from services.agent.conversation.turn import ConversationTurn
from services.agent.conversation.processor import apply_flow_processing

logger = get_logger(__name__)


class ConversationManager:
  """Manages conversation flow and state transitions."""

  def __init__(self, agent_core: AgentCore):
    """Initialize conversation manager."""
    self.agent_core = agent_core
    self.current_flow = ConversationFlow.GREETING
    self.conversation_turns: List[ConversationTurn] = []
    self.conversation_context = {}
    self.error_count = 0
    self.max_errors = 3

  async def process_conversation_turn(
      self,
      user_input: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> AgentResponse:
    """
    Process a conversation turn with flow management.

    Args:
        user_input: User's spoken input (transcribed)
        audio_data: Original audio data
        metadata: Additional metadata

    Returns:
        Agent response with flow management
    """
    try:
      logger.info(
          f"Processing conversation turn in flow: {self.current_flow.value}")

      # Get base response from agent core
      base_response = await self.agent_core.process_user_input(
          user_input, audio_data, metadata
      )

      # Apply flow-specific processing
      flow_response = await apply_flow_processing(
          self.current_flow, user_input, base_response, metadata or {}
      )

      # Record conversation turn
      turn = ConversationTurn(
          user_input=user_input,
          agent_response=flow_response.text,
          timestamp=time.time(),
          flow_state=self.current_flow,
          confidence=flow_response.confidence,
          metadata=flow_response.metadata or {}
      )
      self.conversation_turns.append(turn)

      return flow_response

    except Exception as e:
      logger.error(f"Error in conversation processing: {str(e)}")
      self.error_count += 1

      # Switch to error handling if too many errors
      if self.error_count >= self.max_errors:
        self.current_flow = ConversationFlow.ERROR_HANDLING

      # Create a fallback response
      fallback = AgentResponse(
          text="I'm having trouble understanding. Can you please rephrase that?",
          confidence=0.5,
          action=None,
          metadata={"error": str(e), "recovery": "fallback_response"}
      )

      return fallback
