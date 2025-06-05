"""
Flow-specific processing logic.
"""
from typing import Dict, Any, Optional
import asyncio

from core.logging.setup import get_logger
from services.agent.core import AgentResponse
from services.agent.conversation.flow import ConversationFlow
from services.agent.conversation.handler import (
    handle_greeting, handle_gathering_info, handle_processing_request,
    handle_providing_solution, handle_confirming, handle_closing, handle_error
)

logger = get_logger(__name__)


async def apply_flow_processing(
    current_flow: ConversationFlow,
    user_input: str,
    base_response: AgentResponse,
    context: Dict[str, Any]
) -> AgentResponse:
  """
  Apply flow-specific processing to the response.

  Args:
      current_flow: Current conversation flow state
      user_input: User's input text
      base_response: Base response from agent core
      context: Conversation context

  Returns:
      Processed agent response
  """
  # Apply appropriate flow handler based on current flow state
  if current_flow == ConversationFlow.GREETING:
    return await handle_greeting(user_input, base_response, context)

  elif current_flow == ConversationFlow.GATHERING_INFO:
    return await handle_gathering_info(user_input, base_response, context)

  elif current_flow == ConversationFlow.PROCESSING_REQUEST:
    return await handle_processing_request(user_input, base_response, context)

  elif current_flow == ConversationFlow.PROVIDING_SOLUTION:
    return await handle_providing_solution(user_input, base_response, context)

  elif current_flow == ConversationFlow.CONFIRMING:
    return await handle_confirming(user_input, base_response, context)

  elif current_flow == ConversationFlow.CLOSING:
    return await handle_closing(user_input, base_response, context)

  elif current_flow == ConversationFlow.ERROR_HANDLING:
    return await handle_error(user_input, base_response, context)

  # Default case - return original response
  logger.warning(f"No flow handler for flow state: {current_flow.value}")
  return base_response
