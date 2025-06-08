"""
Main conversation processing coordination.
"""

from typing import Dict, Any, Optional
import time
from core.logging.setup import get_logger
from ..flow.definitions import ConversationFlow, ConversationTurn
from ..state.manager import FlowStateManager
from ..extraction.extractor import InformationExtractor
from ..context.manager import ConversationContextManager
from ..handlers.greeting import GreetingHandler
from ..handlers.gathering import GatheringHandler
from ..handlers.processing import ProcessingHandler
from ..handlers.solution import SolutionHandler
from ..handlers.confirmation import ConfirmationHandler
from ..handlers.closing import ClosingHandler
from ..handlers.error import ErrorHandler

logger = get_logger(__name__)


class ConversationProcessor:
  """Main conversation processing coordinator."""

  def __init__(self, agent_core):
    """Initialize conversation processor."""
    self.agent_core = agent_core

    # Initialize managers
    self.flow_state_manager = FlowStateManager()
    self.extractor = InformationExtractor()
    self.context_manager = ConversationContextManager()

    # Initialize handlers
    self.handlers = {
        ConversationFlow.GREETING: GreetingHandler(agent_core),
        ConversationFlow.GATHERING_INFO: GatheringHandler(self.extractor, self.context_manager),
        ConversationFlow.PROCESSING_REQUEST: ProcessingHandler(),
        ConversationFlow.PROVIDING_SOLUTION: SolutionHandler(),
        ConversationFlow.CONFIRMING: ConfirmationHandler(),
        ConversationFlow.CLOSING: ClosingHandler(),
        ConversationFlow.ERROR_HANDLING: ErrorHandler()
    }

  async def process_turn(
      self,
      user_input: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ):
    """Process a conversation turn with flow management."""
    try:
      logger.info(
          f"Processing conversation turn in flow: {self.flow_state_manager.current_flow.value}")

      # Get base response from agent core
      base_response = await self.agent_core.process_user_input(
          user_input, audio_data, metadata
      )

      # Apply flow-specific processing
      flow_response = await self._apply_flow_processing(
          user_input, base_response, metadata or {}
      )

      # Record conversation turn
      turn = ConversationTurn(
          user_input=user_input,
          agent_response=flow_response.text,
          timestamp=time.time(),
          flow_state=self.flow_state_manager.current_flow,
          confidence=flow_response.confidence,
          metadata=metadata or {}
      )
      self.flow_state_manager.conversation_turns.append(turn)

      # Determine next flow state
      next_flow = await self.flow_state_manager.determine_next_flow(user_input, flow_response)
      if next_flow != self.flow_state_manager.current_flow:
        self.flow_state_manager.set_flow(next_flow)

      # Reset error count on successful processing
      self.flow_state_manager.reset_error_count()

      logger.info(
          f"Conversation turn completed. Next flow: {self.flow_state_manager.current_flow.value}")

      return flow_response

    except Exception as e:
      logger.error(f"Error processing conversation turn: {str(e)}")

      self.flow_state_manager.increment_error_count()

      from services.agent.core import AgentResponse
      return AgentResponse(
          text="I'm having some difficulty understanding. Could you please repeat that?",
          confidence=0.3
      )

  async def _apply_flow_processing(self, user_input: str, base_response, metadata: Dict[str, Any]):
    """Apply flow-specific processing to the response."""
    try:
      current_flow = self.flow_state_manager.current_flow
      handler = self.handlers.get(current_flow)

      if handler:
        if current_flow == ConversationFlow.GREETING:
          return await handler.handle(user_input, base_response, metadata, len(self.flow_state_manager.conversation_turns))
        elif current_flow == ConversationFlow.ERROR_HANDLING:
          return await handler.handle(user_input, base_response, metadata, self.flow_state_manager.error_count)
        else:
          return await handler.handle(user_input, base_response, metadata)
      else:
        logger.warning(f"No handler for flow: {current_flow.value}")
        return base_response

    except Exception as e:
      logger.error(f"Error in flow processing: {str(e)}")
      return base_response

  def get_conversation_flow(self) -> ConversationFlow:
    """Get current conversation flow."""
    return self.flow_state_manager.get_flow()

  def set_conversation_flow(self, flow: ConversationFlow):
    """Set conversation flow."""
    self.flow_state_manager.set_flow(flow)

  async def get_conversation_stats(self) -> Dict[str, Any]:
    """Get conversation statistics."""
    turns = self.flow_state_manager.conversation_turns
    return {
        "current_flow": self.flow_state_manager.current_flow.value,
        "total_turns": len(turns),
        "average_confidence": sum(turn.confidence for turn in turns) / max(len(turns), 1),
        "conversation_context": self.context_manager.get_context(),
        "error_count": self.flow_state_manager.error_count,
        "flows_visited": list(set(turn.flow_state.value for turn in turns))
    }
