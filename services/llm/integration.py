"""
Integration of prompt-based LLM system with the voice agent.
"""
from typing import Dict, Any, Optional, List, TYPE_CHECKING
import asyncio

from core.logging.setup import get_logger
from services.agent.core import AgentCore, AgentResponse
from services.llm.prompt import (
    PromptManager, PromptBuilder, ConversationContext, PromptLLMAdapter
)
from services.llm.orchestrator import LLMOrchestrator
from services.tts.elevenlabs import ElevenLabsService
from models.internal.callcontext import CallContext

if TYPE_CHECKING:
  from services.ringover.streaming import RingoverStreamHandler

logger = get_logger(__name__)


class VoiceAgentLLMIntegration:
  """
  Integration of LLM prompt system with voice agent.

  This class brings together the prompt management, LLM orchestration,
  streaming Ringover audio, and TTS to create a complete voice agent solution.
  """

  def __init__(
      self,
      agent_core: AgentCore,
      llm_orchestrator: LLMOrchestrator,
      prompt_manager: PromptManager,
      tts_service: Optional[ElevenLabsService] = None,
      stream_handler: Optional["RingoverStreamHandler"] = None
  ):
    """
    Initialize the integration.

    Args:
        agent_core: The agent core system
        llm_orchestrator: The LLM orchestrator
        prompt_manager: The prompt template manager
        tts_service: Text-to-speech service
        stream_handler: Optional stream handler for Ringover
    """
    self.agent_core = agent_core
    self.llm_orchestrator = llm_orchestrator
    self.prompt_manager = prompt_manager
    self.tts_service = tts_service
    self.stream_handler = stream_handler

    # Create the LLM adapter
    self.llm_adapter = PromptLLMAdapter(llm_orchestrator, prompt_manager)

    # Default template for calls
    self.default_template = "call_center_agent"
    self.current_context = None

  async def initialize_call(self, call_context: CallContext, template_name: Optional[str] = None):
    """
    Initialize for a new call.

    Args:
        call_context: The call context information
        template_name: Optional template name to use
    """
    # Initialize the agent core
    await self.agent_core.initialize(call_context)

    # Extract caller info from call context
    caller_info = {
        "phone_number": call_context.phone_number,
        "direction": call_context.direction.value,
        "session_id": call_context.session_id,
        **call_context.metadata  # Include any additional metadata
    }

    # Create conversation context
    self.current_context = ConversationContext(
        call_id=call_context.call_id,
        caller_info=caller_info,
        conversation_history=[],
        current_state="greeting"  # Default starting state
    )

    # If we have a stream handler, initialize it
    if self.stream_handler:
      await self.stream_handler.start_session(
          call_id=call_context.call_id,
          caller_info=caller_info,
          context={"template": template_name or self.default_template}
      )

    logger.info(
        f"Initialized call {call_context.call_id} with template {template_name or self.default_template}")

  async def process_user_input(
      self,
      user_input: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> AgentResponse:
    """
    Process user input to generate a response.

    Args:
        user_input: User's input text
        audio_data: Optional audio data
        metadata: Additional metadata

    Returns:
        Agent response
    """
    if not self.current_context:
      raise ValueError("Call not initialized. Call initialize_call first.")

    # Generate response using prompt template
    llm_response = await self.llm_adapter.generate_response_with_prompt(
        context=self.current_context,
        template_name=metadata.get("template") if metadata else None,
        provider=metadata.get("provider", "openai") if metadata else "openai"
    )

    if not llm_response:
      return AgentResponse(
          text="I'm sorry, I'm having trouble understanding. Could you please repeat that?",
          confidence=0.0
      )

    # Extract the response text
    response_text = llm_response.response.get_content()

    # Update the conversation context
    self.current_context = self.llm_adapter.update_conversation_context(
        self.current_context,
        user_input,
        response_text
    )

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

    # Create and return the agent response
    return AgentResponse(
        text=response_text,
        audio_data=audio_response,
        confidence=0.9,  # Could be more sophisticated
        thinking_time=llm_response.response.raw_response.get(
            "thinking_time", 0.0) if llm_response.response.raw_response else 0.0,
        metadata={"prompt_used": llm_response.prompt_used,
                  "state": llm_response.state}
    )

  async def handle_streaming_audio(self, audio_chunk: bytes, metadata: Optional[Dict[str, Any]] = None):
    """
    Handle streaming audio from Ringover.

    Args:
        audio_chunk: Audio data chunk
        metadata: Additional metadata
    """
    if not self.stream_handler:
      logger.warning("No stream handler configured")
      return

    if not self.current_context:
      logger.warning("Call not initialized for streaming")
      return

    await self.stream_handler.handle_audio_chunk(audio_chunk, metadata or {})

  async def end_streaming_utterance(self) -> Optional[AgentResponse]:
    """
    End the current utterance and generate a response.

    Returns:
        Agent response if transcription was successful
    """
    if not self.stream_handler:
      return None

    # Get final transcription
    transcription = await self.stream_handler.end_utterance()

    if not transcription:
      return None

    # Process the transcription to get a response
    return await self.process_user_input(transcription)

  async def transition_state(self, new_state: str) -> bool:
    """
    Transition to a new state.

    Args:
        new_state: The new state to transition to

    Returns:
        Whether transition was successful
    """
    if not self.current_context:
      logger.error("Cannot transition state - no active context")
      return False

    try:
      self.current_context = self.llm_adapter.transition_state(
          self.current_context,
          new_state
      )
      return True
    except Exception as e:
      logger.error(f"Failed to transition to state {new_state}: {e}")
      return False

  async def end_call(self):
    """Clean up resources at the end of a call."""
    # End stream handler session
    if self.stream_handler:
      await self.stream_handler.end_session()

    # Reset context
    self.current_context = None

    logger.info("Call ended and resources cleaned up")
