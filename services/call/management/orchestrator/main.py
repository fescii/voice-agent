"""
Main call orchestrator class.
Coordinates call initiation, session management, and streaming setup.
"""
import uuid
import asyncio
from typing import Optional, Dict, Any

from core.logging.setup import get_logger
from services.ringover.api import CallInfo
from services.ringover.client import RingoverClient
from models.external.ringover.apirequest import RingoverCallRequest
from ..session.manager import SessionManager
from ..assignment.manager import AgentAssignmentManager
from ..coordination.manager import CallCoordinationManager
from ..session.models import CallPriority
from core.config.registry import config_registry
from services.ringover.streaming.service import RingoverStreamingService
from services.ringover.streaming.client import RingoverStreamerClient
from services.audio.streaming.service import AudioStreamService

from .streaming.manager import StreamingManager
from .tasks.audio import AudioProcessingTask

logger = get_logger(__name__)


class CallOrchestrator:
  """
  Main orchestrator for managing call lifecycle and coordination.
  Handles call initiation, session management, and streaming setup.
  """

  def __init__(self, startup_context: Any = None):
    """
    Initialize the call orchestrator.

    Args:
        startup_context: Application startup context for service access
    """
    # Core services
    self.streaming_service = RingoverStreamingService()
    self.audio_service = AudioStreamService()
    self.streaming_manager = StreamingManager(startup_context)

    # Ringover client
    self.ringover_client = RingoverClient()

    # Active tasks tracking
    self.active_audio_tasks: Dict[str, asyncio.Task] = {}

    # Store startup context
    self.startup_context = startup_context

    logger.info("Call orchestrator initialized")

  async def handle_inbound_call(self, call_info: CallInfo, priority: str = "normal") -> Dict[str, Any]:
    """
    Handle an inbound call from Ringover webhook.

    Args:
        call_info: Information about the incoming call
        priority: Priority level for the call

    Returns:
        Dict containing call handling result
    """
    try:
      call_id = str(call_info.call_id)
      logger.info(f"📞 Handling inbound call {call_id}")

      # Generate session and agent IDs
      session_id = str(uuid.uuid4())
      agent_id = "agent_001"  # Default agent for now

      # Start audio processing as background task
      audio_task = AudioProcessingTask(
          call_id=call_id,
          session_id=session_id,
          agent_id=agent_id,
          streaming_manager=self.streaming_manager
      )

      # Start the task as asyncio background task
      task = asyncio.create_task(audio_task.execute())
      self.active_audio_tasks[call_id] = task

      logger.info(
          f"🎵 Audio processing task started for inbound call {call_id}")

      return {
          "success": True,
          "session_id": session_id,
          "call_id": call_id,
          "agent_id": agent_id,
          "message": "Inbound call processed successfully"
      }

    except Exception as e:
      logger.error(f"Failed to handle inbound call: {str(e)}")
      return {
          "success": False,
          "error": str(e),
          "call_id": str(call_info.call_id) if call_info else None
      }

  async def initiate_outbound_call(self, user_id: int, phone_number: str, agent_id: str = "agent_001") -> Dict[str, Any]:
    """
    Initiate an outbound call through Ringover.

    Args:
        user_id: ID of the user initiating the call
        phone_number: Phone number to call
        agent_id: Agent to handle the call

    Returns:
        Dict containing call initiation result
    """
    try:
      logger.info(
          f"📞 Initiating outbound call to {phone_number} for user {user_id}")

      # Generate session ID
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

      # Create Ringover API request
      ringover_request = RingoverCallRequest(
          from_number=from_number_int,
          to_number=to_number_int,
          timeout=60,
          device="ALL",
          clir=False
      )

      # Actually initiate the call through Ringover API
      logger.info(f"Making actual Ringover API call to {phone_number}")
      ringover_response = await self.ringover_client.initiate_call(ringover_request)
      logger.info(f"Ringover API response: {ringover_response}")

      # Parse the response to get call_id
      ringover_call_id = self._extract_call_id(ringover_response, session_id)

      # Start audio processing as background task
      audio_task = AudioProcessingTask(
          call_id=ringover_call_id,
          session_id=session_id,
          agent_id=agent_id,
          streaming_manager=self.streaming_manager
      )

      # Start the task as asyncio background task
      task = asyncio.create_task(audio_task.execute())
      self.active_audio_tasks[ringover_call_id] = task

      logger.info(
          f"🎵 Audio processing task started for call {ringover_call_id}")

      return {
          "success": True,
          "session_id": session_id,
          "call_id": str(ringover_call_id),
          "agent_id": agent_id,
          "phone_number": phone_number,
          "message": "Call initiated successfully"
      }

    except Exception as e:
      logger.error(f"Failed to initiate call to {phone_number}: {str(e)}")
      return {
          "success": False,
          "error": str(e),
          "phone_number": phone_number
      }

  async def handle_outbound_call(self, phone_number: str, agent_id: str = "agent_001", user_id: int = 1) -> Optional[str]:
    """
    Handle an outbound call request from API endpoint.

    Args:
        phone_number: Phone number to call
        agent_id: Agent to handle the call
        user_id: ID of the user initiating the call

    Returns:
        Session ID if successful, None if failed
    """
    try:
      result = await self.initiate_outbound_call(
          user_id=user_id,
          phone_number=phone_number,
          agent_id=agent_id
      )

      if result.get("success"):
        return result.get("session_id")
      else:
        logger.error(f"Failed to handle outbound call: {result.get('error')}")
        return None

    except Exception as e:
      logger.error(f"Error in handle_outbound_call: {e}")
      return None

  async def end_call(self, call_id: str) -> Dict[str, Any]:
    """
    End a call and clean up resources.

    Args:
        call_id: ID of the call to end

    Returns:
        Dict containing call end result
    """
    try:
      logger.info(f"📞 Ending call {call_id}")

      # Cancel any active audio processing task
      if call_id in self.active_audio_tasks:
        task = self.active_audio_tasks[call_id]
        task.cancel()
        del self.active_audio_tasks[call_id]
        logger.info(f"Cancelled audio processing task for call {call_id}")

      # Close streaming service
      try:
        await self.streaming_service.close_stream(call_id)
        logger.info(f"Closed streaming for call {call_id}")
      except Exception as stream_error:
        logger.error(
            f"Error closing stream for call {call_id}: {stream_error}")

      logger.info(f"✅ Call {call_id} ended successfully")

      return {
          "success": True,
          "call_id": call_id,
          "message": "Call ended successfully"
      }

    except Exception as e:
      logger.error(f"Failed to end call {call_id}: {str(e)}")
      return {
          "success": False,
          "error": str(e),
          "call_id": call_id
      }

  def _extract_call_id(self, ringover_response: Any, fallback_session_id: str) -> str:
    """
    Extract call_id from Ringover API response.

    Args:
        ringover_response: Response from Ringover API
        fallback_session_id: Fallback ID if no call_id found

    Returns:
        Extracted call_id as string
    """
    ringover_call_id = None

    if isinstance(ringover_response, dict):
      # Direct callback response
      if "call_id" in ringover_response:
        ringover_call_id = ringover_response["call_id"]
      # If it returned call history instead (error case)
      elif "call_list" in ringover_response and ringover_response["call_list"]:
        logger.warning(
            "Received call history instead of callback response - using latest call")
        latest_call = ringover_response["call_list"][0]
        ringover_call_id = latest_call.get("call_id")

    # Fallback to session_id if no call_id found
    if not ringover_call_id:
      logger.warning("No call_id found in response, using session_id")
      ringover_call_id = fallback_session_id

    # Ensure call_id is a string
    if isinstance(ringover_call_id, int):
      ringover_call_id = str(ringover_call_id)

    return ringover_call_id
