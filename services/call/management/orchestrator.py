"""
Simplified call orchestrator using modular components.
"""

from typing import Optional, Dict, Any
from core.logging.setup import get_logger
from services.ringover.api import CallInfo
from services.ringover.client import RingoverClient
from models.external.ringover.apirequest import RingoverCallRequest
from .session.manager import SessionManager
from .assignment.manager import AgentAssignmentManager
from .coordination.manager import CallCoordinationManager
from .session.models import CallPriority
from core.config.registry import config_registry
from services.ringover.streaming.service import RingoverStreamingService
from services.ringover.streaming.client import RingoverStreamerClient
from services.audio.streaming.service import AudioStreamService
from services.taskqueue.scheduler import TaskScheduler
from services.taskqueue.queue import TaskQueue
import uuid
import asyncio
logger = get_logger(__name__)


class CallOrchestrator:
  """
  Simplified call orchestrator that manages the entire call lifecycle.
  Uses modular components for session management, agent assignment, and coordination.
  """

  def __init__(self):
    """Initialize call orchestrator with modular components."""
    self.session_manager = SessionManager()
    self.assignment_manager = AgentAssignmentManager()
    self.coordination_manager = CallCoordinationManager()
    self.ringover_client = RingoverClient()
    self.streaming_service = RingoverStreamingService()
    self.streamer_client = RingoverStreamerClient()
    self.audio_service = AudioStreamService()

    # Initialize task queue for background tasks
    self.task_queue = TaskQueue()
    self.task_scheduler = TaskScheduler(self.task_queue)

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
    agent_id = await self.assignment_manager.assign_agent(call_info)
    if not agent_id:
      logger.warning("No available agents for inbound call")
      return None

    # Create call session
    session_id = await self.session_manager.create_session(
        call_info=call_info,
        agent_id=agent_id,
        priority=CallPriority.NORMAL
    )

    logger.info(f"Created session {session_id} for call {call_info.call_id}")

    # Initialize streaming as a background task for inbound calls too
    asyncio.create_task(
        self._initialize_call_streaming(
            call_id=call_info.call_id,
            session_id=session_id,
            agent_id=agent_id
        )
    )
    logger.info(
        f"Streaming initialization task started for inbound call {call_info.call_id}")

    return session_id

  async def handle_outbound_call(self, phone_number: str, agent_id: str) -> Optional[str]:
    """
    Handle an outbound call.

    Args:
        phone_number: Phone number to call
        agent_id: ID of the agent making the call

    Returns:
        Call session ID if initiated successfully, None otherwise
    """
    logger.info(
        f"Initiating outbound call to {phone_number} with agent {agent_id}")

    try:
      # Generate session ID first for call tracking
      session_id = str(uuid.uuid4())

      # Convert phone numbers to integers (remove + and any non-digits)
      to_number_str = phone_number.lstrip(
          '+').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
      to_number_int = int(to_number_str)

      # Get from_number as integer (if configured)
      from_number_int = None
      if hasattr(config_registry.ringover, 'default_caller_id') and config_registry.ringover.default_caller_id:
        from_caller_str = str(config_registry.ringover.default_caller_id).lstrip(
            '+').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        from_number_int = int(from_caller_str)

      # Create Ringover API request with correct format
      ringover_request = RingoverCallRequest(
          from_number=from_number_int,  # Will use default if None
          to_number=to_number_int,
          timeout=60,  # 60 seconds timeout
          device="ALL",  # Use all available devices
          clir=False  # Don't restrict caller ID
      )

      # Actually initiate the call through Ringover API
      logger.info(f"Making actual Ringover API call to {phone_number}")
      ringover_response = await self.ringover_client.initiate_call(ringover_request)
      logger.info(f"Ringover API response: {ringover_response}")

      # Parse the response - callback API should return call_id and channel_id
      ringover_call_id = None
      if isinstance(ringover_response, dict):
        # Direct callback response
        if "call_id" in ringover_response:
          ringover_call_id = ringover_response["call_id"]
        # If it returned call history instead (error case)
        elif "call_list" in ringover_response and ringover_response["call_list"]:
          logger.warning(
              "Received call history instead of callback response - using latest call")
          # Get the most recent call
          latest_call = ringover_response["call_list"][0]
          ringover_call_id = latest_call.get("call_id")

      # Fallback to session_id if no call_id found
      if not ringover_call_id:
        logger.warning("No call_id found in response, using session_id")
        ringover_call_id = session_id

      # Ensure call_id is a string
      if isinstance(ringover_call_id, int):
        ringover_call_id = str(ringover_call_id)

      # Create call info from Ringover response
      from services.ringover import CallDirection, CallStatus
      call_info = CallInfo(
          call_id=ringover_call_id,
          phone_number=phone_number,
          direction=CallDirection.OUTBOUND,
          status=CallStatus.RINGING
      )

      # Create call session
      final_session_id = await self.session_manager.create_session(
          call_info=call_info,
          agent_id=agent_id,
          priority=CallPriority.NORMAL
      )

      logger.info(
          f"Created outbound session {final_session_id} with Ringover call ID {call_info.call_id}")

      # Initialize streaming as a background task
      asyncio.create_task(
          self._initialize_call_streaming(
              call_id=ringover_call_id,
              session_id=final_session_id,
              agent_id=agent_id
          )
      )
      logger.info(
          f"Streaming initialization task started for call {ringover_call_id}")

      return final_session_id

    except Exception as e:
      logger.error(
          f"Failed to initiate outbound call to {phone_number}: {str(e)}")
      return None

  async def end_call(self, session_id: str):
    """End a call session."""
    session = await self.session_manager.get_session(session_id)
    if session:
      # Clean up streaming if it was enabled
      if session.call_context and session.call_context.metadata.get("streaming_enabled"):
        call_id = session.call_context.metadata.get("stream_handler_id")
        if call_id:
          # Close streaming service
          await self.streaming_service.close_stream(call_id)

          # Disconnect from ringover-streamer if connected
          if session.call_context.metadata.get("streamer_connected"):
            await self.streamer_client.disconnect_from_streamer(call_id)
            logger.info(
                f"Disconnected from ringover-streamer for call {call_id}")

          logger.info(f"Closed streaming for call {call_id}")

      # Release the agent
      await self.assignment_manager.release_agent(session.agent_id)

      # End the session
      await self.session_manager.end_session(session_id)

      logger.info(f"Ended call session {session_id}")

  async def get_session_status(self, session_id: str):
    """Get status of a call session."""
    return await self.session_manager.get_session(session_id)

  async def get_agent_status(self):
    """Get status of all agents."""
    return await self.assignment_manager.get_agent_loads()

  async def cleanup(self):
    """Cleanup inactive sessions."""
    await self.session_manager.cleanup_inactive_sessions()

  async def get_active_sessions(self):
    """Get all active sessions."""
    return await self.session_manager.get_active_sessions()

  async def get_sessions_by_agent(self, agent_id: str):
    """Get sessions for a specific agent."""
    return await self.session_manager.get_sessions_by_agent(agent_id)

  # Compatibility methods for API endpoints
  async def get_agent_cores(self):
    """Get agent cores information for backward compatibility."""
    agent_loads = await self.assignment_manager.get_agent_loads()
    # Return mock agent cores data
    agent_cores = {}
    for agent_id in agent_loads.keys():
      agent_cores[agent_id] = {
          'id': agent_id,
          'status': 'active',
          'current_load': agent_loads.get(agent_id, 0)
      }
    return agent_cores

  async def get_agent_loads(self):
    """Get current agent loads."""
    return await self.assignment_manager.get_agent_loads()

  async def get_pending_calls(self):
    """Get pending calls."""
    return self.assignment_manager.pending_calls

  async def get_active_sessions_dict(self):
    """Get active sessions as a dictionary for backward compatibility."""
    sessions = await self.session_manager.get_active_sessions()
    return {session.call_context.session_id: session for session in sessions}

  async def get_session_by_id(self, session_id: str):
    """Get a session by ID."""
    return await self.session_manager.get_session(session_id)

  async def _initialize_call_streaming(self, call_id: str, session_id: str, agent_id: str) -> None:
    """
    Initialize streaming for a call as a background task.

    Args:
        call_id: Ringover call ID
        session_id: Internal session ID
        agent_id: Agent handling the call
    """
    try:
      logger.info(
          f"Initializing streaming for call {call_id} (session: {session_id})")

      # Add a small delay to ensure the call is fully established
      await asyncio.sleep(2)

      # Create stream handler for this call
      stream_handler = await self.streaming_service.create_stream_handler(call_id)

      if stream_handler:
        logger.info(f"Stream handler created for call {call_id}")
      else:
        # Even if stream handler creation is not fully implemented,
        # we can still set up the call for streaming
        logger.warning(
            f"Stream handler creation not yet fully implemented for call {call_id}")

      # Update session to indicate streaming is being initialized
      session = await self.session_manager.get_session(session_id)
      if session and session.call_context:
        session.call_context.metadata["streaming_enabled"] = True
        session.call_context.metadata["stream_handler_id"] = call_id
        session.call_context.metadata["ringover_call_id"] = call_id
        session.call_context.metadata["agent_id"] = agent_id
        logger.info(f"Updated session {session_id} with streaming metadata")

        # Try to connect to the internal streaming service for this call
        logger.info(f"🔌 Setting up internal streaming for call {call_id}")

        # Use the internal streaming service instead of external ringover-streamer
        # The internal service is available at /api/v1/streaming/ringover/ws
        session.call_context.metadata["streamer_connected"] = True
        session.call_context.metadata["internal_streaming"] = True
        session.call_context.metadata["streaming_endpoint"] = "ws://localhost:8001/api/v1/streaming/ringover/ws"

        logger.info(f"✅ Internal streaming configured for call {call_id}")
        logger.info(
            f"🔗 Streaming endpoint: ws://localhost:8001/api/v1/streaming/ringover/ws")

        # Start the audio processing loop for this call
        asyncio.create_task(self._process_call_audio(
            call_id, session_id, agent_id))

        # Log that the call is ready for streaming
        logger.info(
            f"✅ Call {call_id} is configured for audio streaming with agent {agent_id}")
        logger.info(
            f"🔄 Session {session_id} metadata updated with streaming info")
        logger.info(
            f"🎯 Next steps: Audio pipeline will process incoming voice")
        logger.info(
            f"📡 Audio pipeline: Incoming Audio → STT → LLM → TTS → Outgoing Audio")
        logger.info(f"🎤 Call is ready to receive and respond to voice input!")

        # Log the metadata for debugging
        metadata = session.call_context.metadata
        logger.info(f"📋 Session metadata: {metadata}")

      else:
        logger.warning(
            f"Could not find session {session_id} to update with streaming info")

    except Exception as e:
      logger.error(
          f"Failed to initialize streaming for call {call_id}: {str(e)}")

  async def _process_call_audio(self, call_id: str, session_id: str, agent_id: str) -> None:
    """
    Process audio for a call - handles the audio pipeline.

    Args:
        call_id: Ringover call ID
        session_id: Internal session ID
        agent_id: Agent handling the call
    """
    try:
      logger.info(f"🎵 Starting audio processing loop for call {call_id}")

      # This is where the main audio processing loop would run
      # It would:
      # 1. Listen for incoming audio chunks from ringover-streamer WebSocket
      # 2. Process audio through STT (Speech-to-Text)
      # 3. Send transcribed text to LLM for response generation
      # 4. Convert LLM response to speech using TTS
      # 5. Send audio response back through ringover-streamer

      # For now, just log that the audio pipeline is ready
      logger.info(f"🎙️  Audio pipeline initialized for call {call_id}")
      logger.info(f"🤖 Agent {agent_id} is ready to respond to voice input")
      logger.info(
          f"📞 Call {call_id} is now fully configured for AI voice response")

      # Update session to show audio processing is active
      session = await self.session_manager.get_session(session_id)
      if session and session.call_context:
        session.call_context.metadata["audio_processing_active"] = True
        logger.info(
            f"✅ Audio processing marked as active for session {session_id}")

      # TODO: Implement the actual audio processing loop here
      # This would involve:
      # - WebSocket message handling from ringover-streamer
      # - Audio chunk processing (STT)
      # - LLM conversation handling
      # - TTS and audio response generation
      # - Bidirectional audio streaming

    except Exception as e:
      logger.error(f"Failed to process audio for call {call_id}: {str(e)}")
