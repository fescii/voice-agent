"""
Manager for handling voice agent script operations.
"""
from typing import Dict, Any, Optional, List, TYPE_CHECKING
import json
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.prompt.manager import PromptManager
from services.llm.script.manager import ScriptManager
from services.llm.script.api import ScriptAPI
from models.internal.callcontext import CallContext
from services.llm.prompt.adapter import PromptLLMAdapter
from services.llm.prompt.builder import ConversationContext

if TYPE_CHECKING:
  from services.agent.core import AgentCore

logger = get_logger(__name__)


class VoiceAgentScriptManager:
  """
  Manager for voice agent script operations.

  This class handles the integration between scripts and voice agents,
  providing methods to apply scripts to ongoing calls and transitions
  between script states.
  """

  def __init__(self,
               agent_core: "AgentCore",
               prompt_manager: PromptManager,
               llm_adapter: PromptLLMAdapter):
    """
    Initialize the voice agent script manager.

    Args:
        agent_core: The agent core system
        prompt_manager: The prompt manager to use
        llm_adapter: The LLM adapter for generating responses
    """
    self.agent_core = agent_core
    self.prompt_manager = prompt_manager
    self.llm_adapter = llm_adapter

    # Create script components
    self.script_manager = ScriptManager(prompt_manager)
    self.script_api = ScriptAPI(self.script_manager)

    # Track active scripts for calls
    self.active_scripts: Dict[str, Dict[str, Any]] = {}

  async def load_script(self, script_data: Dict[str, Any], make_default: bool = False) -> bool:
    """
    Load a script from JSON data.

    Args:
        script_data: The script data to load
        make_default: Whether to make this the default script

    Returns:
        Whether the script was loaded successfully
    """
    result = await self.script_api.load_script_from_json(script_data, make_default)
    return result.get("success", False)

  async def assign_script_to_call(self,
                                  call_id: str,
                                  script_name: str,
                                  initial_state: Optional[str] = None) -> bool:
    """
    Assign a script to an active call.

    Args:
        call_id: ID of the call
        script_name: Name of the script to assign
        initial_state: Optional starting state override

    Returns:
        Whether the script was assigned successfully
    """
    # Check if script exists
    script = self.script_manager.get_script(script_name)
    if not script:
      logger.error(f"Script not found: {script_name}")
      return False

    # Determine initial state
    state = initial_state or script.starting_state
    if not state:
      logger.error(f"No valid starting state for script: {script_name}")
      return False

    # Store active script info
    self.active_scripts[call_id] = {
        "script_name": script_name,
        "current_state": state,
        "history": []
    }

    logger.info(
        f"Assigned script {script_name} to call {call_id} starting at state {state}")
    return True

  async def process_script_turn(self,
                                call_context: CallContext,
                                user_input: str,
                                metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Process a conversation turn using the assigned script.

    Args:
        call_context: The call context
        user_input: User's input
        metadata: Additional metadata

    Returns:
        Response with generated content and next script state
    """
    call_id = call_context.call_id

    # Check if call has an assigned script
    if call_id not in self.active_scripts:
      logger.error(f"No script assigned to call {call_id}")
      return None

    script_info = self.active_scripts[call_id]
    script_name = script_info["script_name"]
    current_state = script_info["current_state"]

    # Extract caller info from call context
    caller_info = {
        "phone_number": call_context.phone_number,
        "direction": call_context.direction.value,
        "session_id": call_context.session_id,
        **call_context.metadata  # Include any additional metadata
    }

    # Create conversation context
    conversation_context = ConversationContext(
        call_id=call_id,
        caller_info=caller_info,
        conversation_history=script_info.get("history", []),
        current_state=current_state
    )

    # Generate response using script
    llm_response = await self.llm_adapter.generate_response_with_script(
        script_name=script_name,
        context=conversation_context,
        additional_variables=metadata
    )

    if not llm_response:
      return None

    # Get response content
    response_text = llm_response.response.get_content()

    # Update conversation history
    updated_context = self.llm_adapter.update_conversation_context(
        conversation_context,
        user_input,
        response_text
    )

    # Store updated history
    script_info["history"] = updated_context.conversation_history

    # Return response and current state
    return {
        "response_text": response_text,
        "current_state": current_state,
        "script_name": script_name
    }

  async def transition_script_state(self,
                                    call_id: str,
                                    new_state: str) -> bool:
    """
    Transition to a new state in the script.

    Args:
        call_id: ID of the call
        new_state: Name of the new state

    Returns:
        Whether the transition was successful
    """
    # Check if call has an assigned script
    if call_id not in self.active_scripts:
      logger.error(f"No script assigned to call {call_id}")
      return False

    script_info = self.active_scripts[call_id]
    script_name = script_info["script_name"]

    # Check if script exists
    script = self.script_manager.get_script(script_name)
    if not script:
      logger.error(f"Script not found: {script_name}")
      return False

    # Check if new state exists in the script
    state_exists = any(state.name == new_state for state in script.states)
    if not state_exists:
      logger.error(f"State {new_state} not found in script {script_name}")
      return False

    # Update current state
    script_info["current_state"] = new_state
    logger.info(
        f"Transitioned call {call_id} to state {new_state} in script {script_name}")

    return True

  def get_current_script_state(self, call_id: str) -> Optional[Dict[str, str]]:
    """
    Get the current script and state for a call.

    Args:
        call_id: ID of the call

    Returns:
        Dictionary with script name and current state
    """
    if call_id not in self.active_scripts:
      return None

    script_info = self.active_scripts[call_id]
    return {
        "script_name": script_info["script_name"],
        "current_state": script_info["current_state"]
    }

  async def end_script_session(self, call_id: str) -> bool:
    """
    End script session for a call.

    Args:
        call_id: ID of the call

    Returns:
        Whether the session was ended successfully
    """
    if call_id in self.active_scripts:
      del self.active_scripts[call_id]
      logger.info(f"Ended script session for call {call_id}")
      return True

    return False
