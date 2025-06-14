"""
Call session management and lifecycle.
"""

from typing import Dict, Optional, List
import uuid
from datetime import datetime, timezone
from core.logging.setup import get_logger
from .models import CallSession, CallPriority
from models.internal.callcontext import CallContext, CallDirection, CallStatus
from services.ringover import CallInfo

logger = get_logger(__name__)


class SessionManager:
  """Manages call sessions and their lifecycle."""

  def __init__(self):
    """Initialize session manager."""
    self.active_sessions: Dict[str, CallSession] = {}

  async def create_session(
      self,
      call_info: CallInfo,
      agent_id: str,
      priority: CallPriority = CallPriority.NORMAL
  ) -> str:
    """Create a new call session."""
    session_id = str(uuid.uuid4())

    call_context = CallContext(
        call_id=str(call_info.call_id),  # Ensure it's a string
        session_id=session_id,
        phone_number=call_info.phone_number,
        agent_id=agent_id,
        direction=CallDirection.INBOUND,
        status=CallStatus.RINGING,
        start_time=datetime.now(),
        end_time=None,
        duration=None,
        ringover_call_id=str(call_info.call_id),  # Ensure it's a string
        websocket_id=None,
        metadata={}
    )

    session = CallSession(
        call_id=call_info.call_id,
        agent_id=agent_id,
        call_context=call_context,
        call_info=call_info,
        priority=priority
    )

    self.active_sessions[session_id] = session
    logger.info(f"Created call session {session_id} for agent {agent_id}")

    return session_id

  async def get_session(self, session_id: str) -> Optional[CallSession]:
    """Get a call session by ID."""
    return self.active_sessions.get(session_id)

  async def update_session_activity(self, session_id: str):
    """Update last activity time for a session."""
    session = self.active_sessions.get(session_id)
    if session:
      session.last_activity = datetime.now()

  async def end_session(self, session_id: str):
    """End and remove a call session."""
    session = self.active_sessions.get(session_id)
    if session:
      session.is_active = False
      session.call_context.end_time = datetime.now()
      session.call_context.status = CallStatus.ENDED

      # Calculate duration
      if session.call_context.start_time:
        duration = session.call_context.end_time - session.call_context.start_time
        session.call_context.duration = int(duration.total_seconds())

      # Remove from active sessions
      del self.active_sessions[session_id]
      logger.info(f"Ended call session {session_id}")

  async def get_active_sessions(self) -> List[CallSession]:
    """Get all active sessions."""
    return list(self.active_sessions.values())

  async def get_sessions_by_agent(self, agent_id: str) -> List[CallSession]:
    """Get all sessions for a specific agent."""
    return [session for session in self.active_sessions.values()
            if session.agent_id == agent_id]

  async def cleanup_inactive_sessions(self, max_age_minutes: int = 60):
    """Clean up old inactive sessions."""
    current_time = datetime.now()
    sessions_to_remove = []

    for session_id, session in self.active_sessions.items():
      age_minutes = (current_time - session.last_activity).total_seconds() / 60
      if age_minutes > max_age_minutes:
        sessions_to_remove.append(session_id)

    for session_id in sessions_to_remove:
      await self.end_session(session_id)
      logger.info(f"Cleaned up inactive session {session_id}")
