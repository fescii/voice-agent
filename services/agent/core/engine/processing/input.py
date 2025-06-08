"""
Input processing and message handling.
"""
import time
from typing import Dict, Any, Optional, List

from core.logging.setup import get_logger
from models.external.llm.response import LLMResponse
from ...state import AgentState
from ...response import AgentResponse

logger = get_logger(__name__)


class InputProcessor:
  """Processes user input and manages conversation flow."""

  def __init__(self, agent_core):
    """Initialize the input processor."""
    self.agent_core = agent_core

  async def process_user_input(
      self,
      user_text: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> AgentResponse:
    """
    Process user input and generate agent response.

    Args:
        user_text: Transcribed user speech
        audio_data: Original audio data
        metadata: Additional metadata

    Returns:
        Agent response
    """
    try:
      start_time = time.time()
      self.agent_core.state = AgentState.THINKING

      logger.info(f"Processing user input: '{user_text[:100]}...'")

      # Add user input to conversation history
      self.agent_core.conversation_history.append({
          "role": "user",
          "content": user_text,
          "timestamp": time.time(),
          "metadata": metadata or {}
      })

      # Generate context for LLM
      context = await self.agent_core.context_manager.build_conversation_context()

      # Get LLM response
      llm_response = await self.agent_core.llm_orchestrator.generate_response(
          messages=context["messages"],
          context=context["metadata"],
          config=context["generation_config"]
      )

      # Process LLM response
      if llm_response:
        agent_response = await self.agent_core.response_processor.process_llm_response(llm_response)
      else:
        # Handle case where LLM failed to respond
        agent_response = AgentResponse(
            text="I apologize, but I'm having trouble processing your request right now.",
            confidence=0.1
        )

      # Add agent response to conversation history
      self.agent_core.conversation_history.append({
          "role": "assistant",
          "content": agent_response.text,
          "timestamp": time.time(),
          "metadata": {
              "confidence": agent_response.confidence,
              "thinking_time": agent_response.thinking_time,
              "action": agent_response.action
          }
      })

      thinking_time = time.time() - start_time
      agent_response.thinking_time = thinking_time

      self.agent_core.state = AgentState.IDLE

      logger.info(
          f"Generated response in {thinking_time:.2f}s: '{agent_response.text[:100]}...'")

      return agent_response

    except Exception as e:
      logger.error(f"Error processing user input: {str(e)}")
      self.agent_core.state = AgentState.ERROR

      # Return error response
      return AgentResponse(
          text="I apologize, but I'm having trouble processing your request right now. Could you please try again?",
          confidence=0.0,
          thinking_time=time.time() - start_time
      )

  async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
    """
    Process a message from a user.

    Args:
        message: User message text
        context: Optional context information

    Returns:
        Agent response
    """
    # This is a wrapper around process_user_input for simpler interface
    return await self.process_user_input(message, metadata=context)
