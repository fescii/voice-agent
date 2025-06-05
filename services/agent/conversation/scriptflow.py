"""
Script-based conversation flow manager.
"""
from typing import Dict, Any, Optional, List
import asyncio
import time
from dataclasses import dataclass

from core.logging.setup import get_logger
from models.internal.callcontext import CallContext
from services.agent.core import AgentCore, AgentResponse
from services.agent.conversation.manager import ConversationManager
from services.agent.conversation.turn import ConversationTurn
from services.agent.conversation.flow import ConversationFlow
from services.llm.script.agent import VoiceAgentScriptManager
from services.llm.prompt.builder import ConversationContext

logger = get_logger(__name__)


@dataclass
class ScriptFlowState:
  """State for script-based conversation flow."""
  call_id: str
  script_name: str
  current_state: str
  is_active: bool = True
  metadata: Optional[Dict[str, Any]] = None


class ScriptConversationFlow:
  """
  Manages script-based conversation flows.

  This class integrates the script management system with the
  conversation manager, allowing for script-driven voice agent
  interactions.
  """

  def __init__(self,
               conversation_manager: ConversationManager,
               script_manager: VoiceAgentScriptManager):
    """
    Initialize the script conversation flow.

    Args:
        conversation_manager: The main conversation manager
        script_manager: The voice agent script manager
    """
    self.conversation_manager = conversation_manager
    self.script_manager = script_manager
    self.active_flows: Dict[str, ScriptFlowState] = {}

  async def activate_script_flow(self,
                                 call_context: CallContext,
                                 script_name: str,
                                 initial_state: Optional[str] = None) -> bool:
    """
    Activate a script-based conversation flow for a call.

    Args:
        call_context: The call context
        script_name: Name of the script to use
        initial_state: Optional initial state

    Returns:
        Whether the script flow was activated successfully
    """
    call_id = call_context.call_id

    # Assign script to call
    success = await self.script_manager.assign_script_to_call(
        call_id, script_name, initial_state
    )

    if not success:
      logger.error(f"Failed to assign script {script_name} to call {call_id}")
      return False

    # Get current script state
    script_state = self.script_manager.get_current_script_state(call_id)
    if not script_state:
      return False

    # Store flow state
    self.active_flows[call_id] = ScriptFlowState(
        call_id=call_id,
        script_name=script_name,
        current_state=script_state["current_state"],
        metadata={
            "activation_time": time.time(),
            "call_context": call_context.__dict__
        }
    )

    logger.info(
        f"Activated script flow for call {call_id} using script {script_name}")
    return True

  async def process_script_turn(self,
                                call_context: CallContext,
                                user_input: str,
                                metadata: Optional[Dict[str, Any]] = None) -> Optional[AgentResponse]:
    """
    Process a conversation turn using the active script.

    Args:
        call_context: The call context
        user_input: User's input text
        metadata: Additional metadata

    Returns:
        Agent response or None if no script is active
    """
    call_id = call_context.call_id

    # Check if script flow is active for this call
    if call_id not in self.active_flows or not self.active_flows[call_id].is_active:
      logger.warning(f"No active script flow for call {call_id}")
      return None

    # Get script result
    result = await self.script_manager.process_script_turn(
        call_context, user_input, metadata
    )

    if not result:
      logger.error(f"Failed to process script turn for call {call_id}")
      return None

    # Update flow state if it changed
    current_state = result.get("current_state")
    if current_state and current_state != self.active_flows[call_id].current_state:
      self.active_flows[call_id].current_state = current_state

    # Create metadata dict
    response_metadata = {
        "script_name": result.get("script_name"),
        "script_state": current_state
    }

    # Add additional metadata if provided
    if metadata:
      response_metadata.update(metadata)

    # Create agent response
    response = AgentResponse(
        text=result.get("response_text", ""),
        action=None,  # Could extract actions from the response if needed
        confidence=1.0,  # Script responses have high confidence
        metadata=response_metadata
    )

    # Record turn in conversation manager's history
    self._record_script_turn(call_id, user_input, response)

    return response

  def _record_script_turn(self,
                          call_id: str,
                          user_input: str,
                          response: AgentResponse):
    """
    Record a script conversation turn in the conversation manager.

    Args:
        call_id: ID of the call
        user_input: User's input
        response: The agent's response
    """
    if hasattr(self.conversation_manager, "conversation_turns"):
      # Create turn metadata
      turn_metadata = {
          "script_flow": True,
          "script_name": self.active_flows[call_id].script_name,
          "script_state": self.active_flows[call_id].current_state
      }

      # Add response metadata if available
      if response.metadata:
        turn_metadata.update(response.metadata)

      # Create conversation turn
      turn = ConversationTurn(
          user_input=user_input,
          agent_response=response.text,
          timestamp=time.time(),
          flow_state=ConversationFlow.PROCESSING_REQUEST,  # Default flow state
          confidence=response.confidence,
          metadata=turn_metadata
      )

      # Add to conversation history
      self.conversation_manager.conversation_turns.append(turn)

  async def transition_script_state(self,
                                    call_id: str,
                                    new_state: str) -> bool:
    """
    Transition to a new state in the script flow.

    Args:
        call_id: ID of the call
        new_state: Name of the new state

    Returns:
        Whether the transition was successful
    """
    # Check if script flow is active
    if call_id not in self.active_flows or not self.active_flows[call_id].is_active:
      logger.warning(f"No active script flow for call {call_id}")
      return False

    # Transition script state
    success = await self.script_manager.transition_script_state(call_id, new_state)

    if success:
      # Update flow state
      self.active_flows[call_id].current_state = new_state
      logger.info(
          f"Transitioned script flow for call {call_id} to state {new_state}")

    return success

  async def deactivate_script_flow(self, call_id: str) -> bool:
    """
    Deactivate script flow for a call.

    Args:
        call_id: ID of the call

    Returns:
        Whether the flow was deactivated successfully
    """
    # Check if script flow exists
    if call_id not in self.active_flows:
      return False

    # End script session
    await self.script_manager.end_script_session(call_id)

    # Mark flow as inactive
    self.active_flows[call_id].is_active = False

    logger.info(f"Deactivated script flow for call {call_id}")
    return True

  def get_active_script_info(self, call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about the active script flow.

    Args:
        call_id: ID of the call

    Returns:
        Dictionary with script flow information or None
    """
    if call_id not in self.active_flows or not self.active_flows[call_id].is_active:
      return None

    flow_state = self.active_flows[call_id]
    script_state = self.script_manager.get_current_script_state(call_id)

    if not script_state:
      return None

    return {
        "script_name": flow_state.script_name,
        "current_state": script_state["current_state"],
        "is_active": flow_state.is_active,
        "metadata": flow_state.metadata
    }
