"""
Advanced call management and orchestration.
"""
import asyncio
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid

from core.logging.setup import get_logger
from core.config import SystemConfiguration, AgentConfiguration
from models.internal.callcontext import CallContext, CallDirection, CallStatus
from services.agent.core import AgentCore
from services.agent.config import AgentConfigurationAdapter
from services.ringover import RingoverAPIClient, RingoverWebSocketStreamer, CallInfo
from services.llm.orchestrator import LLMOrchestrator
from services.audio.processor import AudioProcessor
from services.transcription.realtime import RealtimeTranscription
from services.tts.elevenlabs import ElevenLabsService

logger = get_logger(__name__)


class CallPriority(Enum):
  """Call priority levels."""
  LOW = 1
  NORMAL = 2
  HIGH = 3
  URGENT = 4


@dataclass
class CallSession:
  """Represents an active call session."""
  call_id: str
  agent_id: str
  call_context: CallContext
  call_info: CallInfo
  priority: CallPriority = CallPriority.NORMAL
  created_at: datetime = field(default_factory=datetime.now)
  last_activity: datetime = field(default_factory=datetime.now)
  metadata: Dict[str, Any] = field(default_factory=dict)

  # Session state
  is_active: bool = True
  is_streaming: bool = False
  script_name: Optional[str] = None

  # Performance metrics
  response_times: List[float] = field(default_factory=list)
  error_count: int = 0
  audio_quality_score: Optional[float] = None


class CallOrchestrator:
  """
  Advanced call orchestrator that manages the entire call lifecycle.

  Handles call routing, load balancing, session management,
  and coordination between all voice agent components.
  """

  def __init__(self, system_config: SystemConfiguration):
    """
    Initialize call orchestrator.

    Args:
        system_config: System configuration
    """
    self.system_config = system_config
    self.active_sessions: Dict[str, CallSession] = {}
    self.agent_loads: Dict[str, int] = {}

    # Initialize Ringover client with proper config casting
    from core.config.providers.telephony import RingoverConfig
    if isinstance(system_config.telephony_config, RingoverConfig):
      ringover_config = system_config.telephony_config
    else:
      # Create RingoverConfig from TelephonyConfig
      ringover_config = RingoverConfig(
          provider=system_config.telephony_config.provider,
          api_key=system_config.telephony_config.api_key,
          api_secret=system_config.telephony_config.api_secret,
          webhook_secret=system_config.telephony_config.webhook_secret,
          base_url=system_config.telephony_config.base_url,
          websocket_url=system_config.telephony_config.websocket_url
      )
    self.ringover_client = RingoverAPIClient(ringover_config)

    # Component managers
    self.llm_orchestrator = LLMOrchestrator()
    self.audio_processor = AudioProcessor()
    # Initialize services with proper configuration
    from services.transcription.processor import TranscriptionProcessor
    from core.config.services.stt.whisper import WhisperConfig

    # Create a default whisper config - TODO: get from system config
    whisper_config = WhisperConfig(
        api_key=system_config.default_stt_config.api_key if system_config.default_stt_config else "",
        model="whisper-1"
    )
    transcription_processor = TranscriptionProcessor(whisper_config)
    self.transcription_service = RealtimeTranscription(transcription_processor)

    # Initialize TTS service with default config or first agent's config
    tts_config = system_config.default_tts_config
    if not tts_config and system_config.agents:
      tts_config = system_config.agents[0].tts_config
    if tts_config:
      from core.config.services.tts.elevenlabs import ElevenLabsConfig
      elevenlabs_config = ElevenLabsConfig(
          api_key=tts_config.api_key,
          voice_id=tts_config.voice_id
      )
      self.tts_service = ElevenLabsService(elevenlabs_config)
    else:
      self.tts_service = None

    # Agent cores
    self.agent_cores: Dict[str, AgentCore] = {}
    self._initialize_agents()

    # Call queue for load balancing
    self.pending_calls: List[CallInfo] = []
    self.call_assignment_lock = asyncio.Lock()

  def _initialize_agents(self):
    """Initialize agent cores from configuration."""
    for agent_config in self.system_config.agents:
      # Convert AgentConfiguration to AgentConfig-compatible proxy
      agent_config_proxy = AgentConfigurationAdapter.from_app_config(
          agent_config)
      agent_core = AgentCore(agent_config_proxy, self.llm_orchestrator)
      self.agent_cores[agent_config.agent_id] = agent_core
      self.agent_loads[agent_config.agent_id] = 0

  async def handle_inbound_call(self, call_info: CallInfo) -> Optional[str]:
    """
    Handle an incoming call.

    Args:
        call_info: Information about the incoming call

    Returns:
        Call session ID if handled successfully, None otherwise
    """
    logger.info(f"Handling inbound call from {call_info.phone_number}")

    # Find available agent
    agent_id = await self._assign_agent(call_info)
    if not agent_id:
      logger.warning("No available agents for inbound call")
      return None

    # Create call session
    session_id = str(uuid.uuid4())
    call_context = CallContext(
        call_id=call_info.call_id,
        session_id=session_id,
        phone_number=call_info.phone_number,
        agent_id=agent_id,
        direction=CallDirection.INBOUND,
        status=CallStatus.RINGING,
        start_time=datetime.now(),
        end_time=None,
        duration=None,
        ringover_call_id=call_info.call_id,
        websocket_id=None,
        metadata=call_info.metadata or {}
    )

    # Create session
    session = CallSession(
        call_id=call_info.call_id,
        agent_id=agent_id,
        call_context=call_context,
        call_info=call_info
    )

    self.active_sessions[session_id] = session
    self.agent_loads[agent_id] += 1

    # Initialize agent for this call
    agent_core = self.agent_cores[agent_id]
    await agent_core.initialize(call_context)

    # Answer the call
    success = await self.ringover_client.answer_call(call_info.call_id, agent_id)
    if not success:
      logger.error(f"Failed to answer call {call_info.call_id}")
      await self._cleanup_session(session_id)
      return None

    # Start audio streaming
    await self._start_audio_streaming(session)

    logger.info(f"Successfully handled inbound call, session: {session_id}")
    return session_id

  async def initiate_outbound_call(self,
                                   to_number: str,
                                   agent_id: str,
                                   script_name: Optional[str] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Initiate an outbound call.

    Args:
        to_number: Target phone number
        agent_id: ID of the agent making the call
        script_name: Optional script to use
        metadata: Additional call metadata

    Returns:
        Call session ID if successful, None otherwise
    """
    logger.info(
        f"Initiating outbound call to {to_number} with agent {agent_id}")

    # Check agent availability
    agent_config = next(
        (a for a in self.system_config.agents if a.agent_id == agent_id), None)
    if not agent_config:
      logger.error(f"Agent {agent_id} not found")
      return None

    current_load = self.agent_loads.get(agent_id, 0)
    if current_load >= agent_config.max_concurrent_calls:
      logger.warning(f"Agent {agent_id} at capacity ({current_load} calls)")
      return None

    # Get agent's phone number
    from_number = agent_config.personality.get("phone_number")
    if not from_number:
      logger.error(f"No phone number configured for agent {agent_id}")
      return None

    # Initiate call through Ringover
    call_info = await self.ringover_client.initiate_outbound_call(
        to_number=to_number,
        from_number=from_number,
        agent_id=agent_id,
        metadata=metadata
    )

    if not call_info:
      logger.error(f"Failed to initiate outbound call to {to_number}")
      return None

    # Create session
    session_id = str(uuid.uuid4())
    call_context = CallContext(
        call_id=call_info.call_id,
        session_id=session_id,
        phone_number=to_number,
        agent_id=agent_id,
        direction=CallDirection.OUTBOUND,
        status=CallStatus.RINGING,
        start_time=datetime.now(),
        end_time=None,
        duration=None,
        ringover_call_id=call_info.call_id,
        websocket_id=None,
        metadata=metadata or {}
    )

    session = CallSession(
        call_id=call_info.call_id,
        agent_id=agent_id,
        call_context=call_context,
        call_info=call_info,
        script_name=script_name
    )

    self.active_sessions[session_id] = session
    self.agent_loads[agent_id] += 1

    # Initialize agent
    agent_core = self.agent_cores[agent_id]
    await agent_core.initialize(call_context)

    logger.info(f"Successfully initiated outbound call, session: {session_id}")
    return session_id

  async def end_call(self, session_id: str) -> bool:
    """
    End a call session.

    Args:
        session_id: ID of the session to end

    Returns:
        True if ended successfully, False otherwise
    """
    session = self.active_sessions.get(session_id)
    if not session:
      logger.warning(f"Session {session_id} not found")
      return False

    logger.info(f"Ending call session {session_id}")

    # Hang up call
    await self.ringover_client.hang_up_call(session.call_id)

    # Stop audio streaming
    if session.is_streaming:
      # Implementation depends on streaming setup
      pass

    # Cleanup session
    await self._cleanup_session(session_id)

    return True

  async def _assign_agent(self, call_info: CallInfo) -> Optional[str]:
    """
    Assign an agent to a call using load balancing.

    Args:
        call_info: Information about the call

    Returns:
        Agent ID if available, None otherwise
    """
    async with self.call_assignment_lock:
      available_agents = []

      for agent_config in self.system_config.agents:
        current_load = self.agent_loads.get(agent_config.agent_id, 0)
        if current_load < agent_config.max_concurrent_calls:
          available_agents.append((agent_config.agent_id, current_load))

      if not available_agents:
        return None

      # Sort by load (least loaded first)
      available_agents.sort(key=lambda x: x[1])
      return available_agents[0][0]

  async def _start_audio_streaming(self, session: CallSession):
    """
    Start audio streaming for a call session.

    Args:
        session: Call session
    """
    try:
      # Create WebSocket streamer - cast TelephonyConfig to RingoverConfig
      # In practice, system_config.telephony_config should already be RingoverConfig
      from core.config.providers.telephony import RingoverConfig
      if isinstance(self.system_config.telephony_config, RingoverConfig):
        ringover_config = self.system_config.telephony_config
      else:
        # Create RingoverConfig from TelephonyConfig
        ringover_config = RingoverConfig(
            provider=self.system_config.telephony_config.provider,
            api_key=self.system_config.telephony_config.api_key,
            api_secret=self.system_config.telephony_config.api_secret,
            webhook_secret=self.system_config.telephony_config.webhook_secret,
            base_url=self.system_config.telephony_config.base_url,
            websocket_url=self.system_config.telephony_config.websocket_url
        )
      streamer = RingoverWebSocketStreamer(ringover_config)

      # Set up audio handler
      async def audio_handler(audio_frame):
        return await self._process_audio_frame(session, audio_frame)

      streamer.set_audio_handler(audio_handler)

      # Connect to streaming
      auth_token = self.system_config.telephony_config.api_key
      success = await streamer.connect(session.call_id, auth_token)

      if success:
        session.is_streaming = True
        logger.info(
            f"Started audio streaming for session {session.call_context.session_id}")
      else:
        logger.error(
            f"Failed to start audio streaming for session {session.call_context.session_id}")

    except Exception as e:
      logger.error(f"Error starting audio streaming: {e}")

  async def _process_audio_frame(self, session: CallSession, audio_frame) -> Optional[bytes]:
    """
    Process incoming audio frame and generate response.

    Args:
        session: Call session
        audio_frame: Incoming audio data

    Returns:
        Response audio data if available
    """
    try:
      # Update session activity
      session.last_activity = datetime.now()

      # Transcribe audio using the transcription processor
      transcription_result = await self.transcription_service.processor.transcribe_audio(
          audio_frame.audio_data,
          session.call_context
      )

      # Extract text from transcription result
      transcription = transcription_result.full_text if transcription_result else ""

      if not transcription.strip():
        return None

      # Get agent response
      # TODO: Create agent core on demand or fix configuration adapter
      if session.agent_id not in self.agent_cores:
        logger.warning(
            f"Agent core not initialized for agent {session.agent_id}")
        return None

      agent_core = self.agent_cores[session.agent_id]
      response = await agent_core.process_user_input(
          transcription,
          audio_frame.audio_data
      )

      if not response or not response.text:
        return None

      # Convert response to speech
      if self.tts_service:
        audio_data = await self.tts_service.synthesize_speech(
            response.text
            # TODO: Get voice_id from agent configuration
        )
      else:
        logger.warning("TTS service not available")
        audio_data = None

      # Track performance
      session.response_times.append(
          (datetime.now() - session.last_activity).total_seconds()
      )

      return audio_data

    except Exception as e:
      logger.error(f"Error processing audio frame: {e}")
      session.error_count += 1
      return None

  async def _cleanup_session(self, session_id: str):
    """
    Cleanup a call session.

    Args:
        session_id: ID of the session to cleanup
    """
    session = self.active_sessions.get(session_id)
    if session:
      # Update agent load
      self.agent_loads[session.agent_id] -= 1

      # Mark session as inactive
      session.is_active = False

      # Remove from active sessions
      del self.active_sessions[session_id]

      logger.info(f"Cleaned up session {session_id}")

  def get_system_status(self) -> Dict[str, Any]:
    """
    Get system status and metrics.

    Returns:
        System status dictionary
    """
    active_calls = len(self.active_sessions)
    total_capacity = sum(
        agent.max_concurrent_calls
        for agent in self.system_config.agents
    )

    return {
        "active_calls": active_calls,
        "total_capacity": total_capacity,
        "utilization": active_calls / total_capacity if total_capacity > 0 else 0,
        "agent_loads": self.agent_loads.copy(),
        "pending_calls": len(self.pending_calls),
        "system_health": "healthy" if active_calls < total_capacity * 0.9 else "at_capacity"
    }

  def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a call session.

    Args:
        session_id: ID of the session

    Returns:
        Session information if found, None otherwise
    """
    session = self.active_sessions.get(session_id)
    if not session:
      return None

    return {
        "session_id": session_id,
        "call_id": session.call_id,
        "agent_id": session.agent_id,
        "phone_number": session.call_context.phone_number,
        "direction": session.call_context.direction.value,
        "status": session.call_context.status.value,
        "duration": (datetime.now() - session.created_at).total_seconds(),
        "is_active": session.is_active,
        "is_streaming": session.is_streaming,
        "script_name": session.script_name,
        "error_count": session.error_count,
        "avg_response_time": sum(session.response_times) / len(session.response_times) if session.response_times else 0
    }
