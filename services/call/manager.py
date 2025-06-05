"""
Call Manager - High-level call management service
"""
from typing import Dict, Any, Optional
import asyncio

from services.call.management.supervisor import CallSupervisor
from services.call.initiation.outbound import OutboundCallService
from services.call.state.manager import CallStateManager
from core.logging.setup import get_logger

logger = get_logger(__name__)


class CallManager:
  """High-level service for managing calls."""

  def __init__(self):
    """Initialize call manager."""
    self.supervisor = CallSupervisor()
    self.outbound_service = OutboundCallService()
    self.state_manager = CallStateManager()
    self.logger = logger

  async def initiate_call(self, phone_number: str, agent_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Initiate an outbound call.

    Args:
        phone_number: Phone number to call
        agent_id: Agent ID to assign
        context: Additional context

    Returns:
        Call initiation result
    """
    try:
      result = await self.outbound_service.initiate_call(
          phone_number=phone_number,
          agent_id=agent_id,
          context=context or {}
      )
      return {
          "call_id": result.call_id,
          "status": result.status.value,
          "ringover_call_id": result.ringover_call_id,
          "error_message": result.error_message,
          "metadata": result.metadata
      }
    except Exception as e:
      self.logger.error(f"Failed to initiate call: {e}")
      return {"error": str(e)}

  async def end_call(self, call_id: str) -> Dict[str, Any]:
    """
    End an active call.

    Args:
        call_id: Call ID to end

    Returns:
        Call end result
    """
    try:
      success = await self.supervisor.end_call(call_id)
      return {
          "success": success,
          "call_id": call_id,
          "message": "Call ended successfully" if success else "Failed to end call"
      }
    except Exception as e:
      self.logger.error(f"Failed to end call: {e}")
      return {"success": False, "error": str(e)}

  async def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get call status.

    Args:
        call_id: Call ID

    Returns:
        Call status or None if not found
    """
    try:
      state = await self.state_manager.get_state(call_id)
      if state is None:
        return None
      return {
          "call_id": state.call_id,
          "state": state.state.value,
          "previous_state": state.previous_state.value if state.previous_state else None,
          "timestamp": state.timestamp.isoformat(),
          "agent_id": state.agent_id,
          "user_id": state.user_id,
          "metadata": state.metadata
      }
    except Exception as e:
      self.logger.error(f"Failed to get call status: {e}")
      return None

  async def transfer_call(self, call_id: str, target_agent_id: str) -> Dict[str, Any]:
    """
    Transfer a call to another agent.

    Args:
        call_id: Call ID to transfer
        target_agent_id: Target agent ID

    Returns:
        Transfer result
    """
    try:
      success = await self.supervisor.transfer_call(call_id, target_agent_id)
      return {
          "success": success,
          "call_id": call_id,
          "target_agent_id": target_agent_id,
          "message": "Call transferred successfully" if success else "Failed to transfer call"
      }
    except Exception as e:
      self.logger.error(f"Failed to transfer call: {e}")
      return {"success": False, "error": str(e)}

  async def get_active_call_count(self) -> int:
    """
    Get the count of active calls.

    Returns:
        Number of active calls
    """
    try:
      active_calls = await self.state_manager.get_active_calls()
      return len(active_calls)
    except Exception as e:
      self.logger.error(f"Failed to get active call count: {e}")
      return 0
