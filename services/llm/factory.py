"""
Factory for creating LLM prompt-based voice agent systems.
"""
from typing import Optional, Dict, Any, TYPE_CHECKING

from services.llm.prompt import PromptManager
from services.llm.prompt.templates import (
    create_single_prompt_template,
    create_call_center_agent_template,
    create_sales_agent_template
)
from services.llm.orchestrator import LLMOrchestrator
from services.tts.elevenlabs import ElevenLabsService
from services.stt.whisper import WhisperService
from services.llm.prompt.builder import PromptBuilder
from services.llm.integration import VoiceAgentLLMIntegration
from data.db.models.agentconfig import AgentConfig
from core.config.services.tts.elevenlabs import ElevenLabsConfig

if TYPE_CHECKING:
  from services.agent.core import AgentCore

if TYPE_CHECKING:
  from services.ringover.streaming import RingoverStreamHandler
from core.config.services.stt.whisper import WhisperConfig


def create_prompt_manager() -> PromptManager:
  """Create and initialize the prompt manager with built-in templates."""
  manager = PromptManager()

  # Register built-in templates
  manager.register_template(
      create_call_center_agent_template(), make_default=True)
  manager.register_template(create_sales_agent_template())

  # Create a basic single prompt template
  basic_template = create_single_prompt_template(
      name="basic_agent",
      identity="You are a friendly AI voice assistant helping users over the phone.",
      style="Speak in a natural, conversational tone. Keep responses concise and focused.",
      tasks="Answer user questions and provide helpful information.",
      guidelines="Always be polite and respectful. If you don't know something, admit it.",
      tools=["end_call", "transfer_call"]
  )
  manager.register_template(basic_template)

  return manager


def create_integrated_voice_agent(
    agent_config: AgentConfig,
    llm_orchestrator: LLMOrchestrator,
    tts_config: Optional[ElevenLabsConfig] = None,
    stt_config: Optional[WhisperConfig] = None,
    enable_streaming: bool = False
) -> VoiceAgentLLMIntegration:
  """
  Create an integrated voice agent system.

  Args:
      agent_config: Configuration for the agent
      llm_orchestrator: LLM orchestrator instance
      tts_config: Text-to-speech configuration
      stt_config: Speech-to-text configuration
      enable_streaming: Whether to enable streaming audio/transcription

  Returns:
      Integrated voice agent system
  """
  # Create the agent core
  from services.agent.core import AgentCore
  agent_core = AgentCore(agent_config, llm_orchestrator)

  # Create the prompt manager
  prompt_manager = create_prompt_manager()

  # Create TTS service
  tts_service = ElevenLabsService(tts_config) if tts_config else None

  # Create streaming components if enabled
  stream_handler = None
  if enable_streaming and stt_config:
    # Import locally to avoid circular dependency
    from services.ringover.streaming import RingoverStreamHandler

    stt_service = WhisperService(stt_config)
    prompt_builder = PromptBuilder(prompt_manager)
    stream_handler = RingoverStreamHandler(stt_service, prompt_builder)

  # Create the integrated system
  integration = VoiceAgentLLMIntegration(
      agent_core=agent_core,
      llm_orchestrator=llm_orchestrator,
      prompt_manager=prompt_manager,
      tts_service=tts_service,
      stream_handler=stream_handler
  )

  return integration
