"""
Call session management and status endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Any, Dict, List, Optional

from api.v1.schemas.response.call import CallStatus
from services.call.management.orchestrator import CallOrchestrator, CallSession
from core.config.app import ConfigurationManager
from core.security.auth.token import get_current_user
from core.logging.setup import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Global orchestrator instance
_orchestrator: Optional[CallOrchestrator] = None


def get_orchestrator() -> CallOrchestrator:
  """Get or create call orchestrator instance."""
  global _orchestrator
  if _orchestrator is None:
    config_manager = ConfigurationManager()
    system_config = config_manager.get_configuration()
    _orchestrator = CallOrchestrator(system_config)
  return _orchestrator


@router.get("/{session_id}/status")
async def get_call_session_status(
    session_id: str,
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
  """
  Get detailed status information for a call session.

  Args:
      session_id: Call session identifier
      current_user: Authenticated user

  Returns:
      Detailed call session status
  """
  try:
    orchestrator = get_orchestrator()
    session = orchestrator.active_sessions.get(session_id)

    if not session:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Call session not found"
      )

    # Build comprehensive status response
    return {
        "session_id": session_id,
        "call_id": session.call_info.call_id,
        "agent_id": session.agent_id,
        "phone_number": session.call_context.phone_number,
        "direction": session.call_context.direction,
        "status": session.call_context.status,
        "priority": session.priority.name,
        "is_active": session.is_active,
        "is_streaming": session.is_streaming,
        "script_name": session.script_name,
        "created_at": session.created_at.isoformat(),
        "last_activity": session.last_activity.isoformat(),
        "start_time": session.call_context.start_time.isoformat() if session.call_context.start_time else None,
        "duration": session.call_context.duration,
        "metadata": session.metadata,
        "performance": {
            "response_times": session.response_times,
            "error_count": session.error_count,
            "audio_quality_score": session.audio_quality_score
        }
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Error getting call session status for {session_id}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )


@router.get("/")
async def list_active_sessions(
    current_user: Any = Depends(get_current_user)
) -> List[Dict[str, Any]]:
  """
  List all active call sessions.

  Args:
      current_user: Authenticated user

  Returns:
      List of active call sessions
  """
  try:
    orchestrator = get_orchestrator()

    sessions = []
    for session_id, session in orchestrator.active_sessions.items():
      sessions.append({
          "session_id": session_id,
          "call_id": session.call_info.call_id,
          "agent_id": session.agent_id,
          "phone_number": session.call_context.phone_number,
          "direction": session.call_context.direction,
          "status": session.call_context.status,
          "priority": session.priority.name,
          "is_active": session.is_active,
          "created_at": session.created_at.isoformat(),
          "last_activity": session.last_activity.isoformat()
      })

    return sessions

  except Exception as e:
    logger.error(f"Error listing active sessions: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )


@router.post("/{session_id}/end")
async def end_call_session(
    session_id: str,
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
  """
  End a call session.

  Args:
      session_id: Call session identifier
      current_user: Authenticated user

  Returns:
      Session termination result
  """
  try:
    orchestrator = get_orchestrator()

    if session_id not in orchestrator.active_sessions:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Call session not found"
      )

    success = await orchestrator.end_call(session_id)

    if not success:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Failed to end call session"
      )

    return {
        "session_id": session_id,
        "status": "ended",
        "message": "Call session ended successfully"
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Error ending call session {session_id}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )


@router.get("/stats/agents")
async def get_agent_load_stats(
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
  """
  Get agent load and performance statistics.

  Args:
      current_user: Authenticated user

  Returns:
      Agent load statistics
  """
  try:
    orchestrator = get_orchestrator()

    stats = {
        "total_agents": len(orchestrator.agent_cores),
        "agent_loads": orchestrator.agent_loads,
        "active_sessions_count": len(orchestrator.active_sessions),
        "pending_calls_count": len(orchestrator.pending_calls),
        "agents": []
    }

    # Get detailed agent information
    for agent_id, agent_core in orchestrator.agent_cores.items():
      current_load = orchestrator.agent_loads.get(agent_id, 0)
      agent_config = next(
          (a for a in orchestrator.system_config.agents if a.agent_id == agent_id), None)
      max_concurrent = agent_config.max_concurrent_calls if agent_config else 0

      stats["agents"].append({
          "agent_id": agent_id,
          "current_load": current_load,
          "max_concurrent_calls": max_concurrent,
          "utilization": (current_load / max_concurrent) * 100 if max_concurrent > 0 else 0,
          "is_available": current_load < max_concurrent
      })

    return stats

  except Exception as e:
    logger.error(f"Error getting agent load stats: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )


@router.post("/{session_id}/script")
async def update_session_script(
    session_id: str,
    script_data: Dict[str, Any],
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
  """
  Update the script for a call session.

  Args:
      session_id: Call session identifier
      script_data: New script data
      current_user: Authenticated user

  Returns:
      Script update result
  """
  try:
    orchestrator = get_orchestrator()
    session = orchestrator.active_sessions.get(session_id)

    if not session:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Call session not found"
      )

    script_name = script_data.get("script_name")
    if script_name:
      session.script_name = script_name

      # Update the agent's script if possible
      agent_core = orchestrator.agent_cores.get(session.agent_id)
      if agent_core:
        # Use the new script update functionality
        try:
          script_updated = await agent_core.update_script(script_name)
          if script_updated:
            logger.info(
                f"Script updated for agent {session.agent_id}: {script_name}")
          else:
            logger.warning(
                f"Failed to update script for agent {session.agent_id}: {script_name}")
        except Exception as e:
          logger.error(
              f"Error updating script for agent {session.agent_id}: {e}")

    return {
        "session_id": session_id,
        "script_name": session.script_name,
        "status": "updated",
        "message": "Session script updated successfully"
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Error updating session script for {session_id}: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=str(e)
    )
