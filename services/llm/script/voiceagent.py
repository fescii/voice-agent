"""
Manager for script-driven voice agent interactions.
"""
from typing import Dict, Any, Optional, List, Union
import json
from pathlib import Path

from core.logging.setup import get_logger
from models.internal.callcontext import CallContext
from services.agent.core import AgentCore, AgentResponse
from services.llm.prompt.adapter import PromptLLMAdapter
from services.llm.prompt.manager import PromptManager
from services.llm.script.agent import VoiceAgentScriptManager
from services.llm.script.api import ScriptAPI
from services.tts.elevenlabs import ElevenLabsService

logger = get_logger(__name__)


class ScriptedVoiceAgentManager:
  """
  Manager for scripted voice agent interactions.

  This class provides high-level methods for creating and managing
  scripted voice agents for calls.
  """

  def __init__(self,
               agent_core: AgentCore,
               prompt_manager: PromptManager,
               llm_adapter: PromptLLMAdapter,
               tts_service: Optional[ElevenLabsService] = None):
    """
    Initialize the scripted voice agent manager.

    Args:
        agent_core: The agent core system
        prompt_manager: The prompt manager to use
        llm_adapter: The LLM adapter for generating responses
        tts_service: Optional text-to-speech service
    """
    self.agent_core = agent_core
    self.prompt_manager = prompt_manager
    self.llm_adapter = llm_adapter
    self.tts_service = tts_service

    # Create script manager
    self.script_manager = VoiceAgentScriptManager(
        agent_core=agent_core,
        prompt_manager=prompt_manager,
        llm_adapter=llm_adapter
    )

    # Create script API
    self.script_api = ScriptAPI(self.script_manager.script_manager)

  async def load_script(self, source: Union[str, Path, Dict[str, Any]]) -> bool:
    """
    Load a script from various sources.

    Args:
        source: Source of the script (file path, JSON string, or dict)

    Returns:
        Whether the script was loaded successfully
    """
    try:
      # Handle different source types
      if isinstance(source, dict):
        # Direct dictionary input
        script = await self.script_manager.load_script(source)
        return script
      elif isinstance(source, (str, Path)):
        path = Path(source) if isinstance(source, str) else source
        if path.exists():
          if path.is_dir():
            # It's a directory
            scripts = await self.script_manager.script_manager.load_scripts_from_directory(str(path))
            return len(scripts) > 0
          else:
            # It's a file - load from the script manager's loader
            script = await self.script_manager.script_manager.load_and_register_script(str(path))
            return script is not None
        else:
          # It's a JSON string
          data = json.loads(str(source))
          return await self.script_manager.load_script(data)

      return False
    except Exception as e:
      logger.error(f"Failed to load script from source: {e}")
      return False

  async def create_scripted_agent(self,
                                  call_context: CallContext,
                                  script_name: str,
                                  initial_state: Optional[str] = None) -> bool:
    """
    Create a scripted agent for a call.

    Args:
        call_context: The call context
        script_name: Name of the script to use
        initial_state: Optional starting state override

    Returns:
        Whether the agent was created successfully
    """
    # Initialize the agent core for this call
    await self.agent_core.initialize(call_context)

    # Assign script to the call
    return await self.script_manager.assign_script_to_call(
        call_id=call_context.call_id,
        script_name=script_name,
        initial_state=initial_state
    )

  async def process_user_input(self,
                               call_context: CallContext,
                               user_input: str,
                               audio_data: Optional[bytes] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> Optional[AgentResponse]:
    """
    Process user input with the scripted agent.

    Args:
        call_context: The call context
        user_input: User's input text
        audio_data: Optional audio data
        metadata: Additional metadata

    Returns:
        Agent response
    """
    # Process through script
    result = await self.script_manager.process_script_turn(
        call_context=call_context,
        user_input=user_input,
        metadata=metadata
    )

    if not result:
      logger.error(
          f"Failed to process script turn for call {call_context.call_id}")
      return None

    response_text = result["response_text"]

    # Generate audio if TTS is available
    audio_response = None
    if self.tts_service:
      try:
        audio_response = await self.tts_service.synthesize_speech(
            response_text,
            voice_id=metadata.get("voice_id") if metadata else None
        )
      except Exception as e:
        logger.error(f"Failed to generate speech: {e}")

    # Create agent response
    return AgentResponse(
        text=response_text,
        audio_data=audio_response,
        confidence=0.9,
        thinking_time=0.0,
        metadata={
            "script_name": result["script_name"],
            "state": result["current_state"]
        }
    )

  async def transition_state(self, call_id: str, new_state: str) -> bool:
    """
    Transition to a new state in the script.

    Args:
        call_id: ID of the call
        new_state: Name of the new state

    Returns:
        Whether the transition was successful
    """
    return await self.script_manager.transition_script_state(call_id, new_state)

  def get_current_state(self, call_id: str) -> Optional[Dict[str, str]]:
    """
    Get the current script and state for a call.

    Args:
        call_id: ID of the call

    Returns:
        Dictionary with script name and current state
    """
    return self.script_manager.get_current_script_state(call_id)

  async def end_call(self, call_id: str) -> bool:
    """
    End a scripted call.

    Args:
        call_id: ID of the call

    Returns:
        Whether the call was ended successfully
    """
    return await self.script_manager.end_script_session(call_id)

  async def get_example_script(self, script_type: str) -> Dict[str, Any]:
    """
    Get an example script.

    Args:
        script_type: Type of example script to get

    Returns:
        Example script JSON
    """
    return await self.script_api.get_example_script(script_type)

  async def list_scripts(self) -> List[Dict[str, Any]]:
    """
    List all loaded scripts.

    Returns:
        List of script summaries
    """
    return await self.script_api.list_loaded_scripts()
