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
import uuid
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
      return final_session_id

    except Exception as e:
      logger.error(
          f"Failed to initiate outbound call to {phone_number}: {str(e)}")
      return None

  async def end_call(self, session_id: str):
    """End a call session."""
    session = await self.session_manager.get_session(session_id)
    if session:
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
