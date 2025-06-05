"""
Agent action handling for call control.
"""
from typing import Dict, Any, Optional
from core.logging.setup import get_logger
from ..core.response import AgentResponse

logger = get_logger(__name__)


class ActionHandler:
  """Handles call-specific actions for agents."""

  def __init__(self, agent_core):
    """Initialize action handler with agent core reference."""
    self.agent_core = agent_core

  async def handle_call_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> AgentResponse:
    """
    Handle call-specific actions.

    Args:
        action: Action to perform (transfer, hold, etc.)
        params: Action parameters

    Returns:
        Agent response acknowledging the action
    """
    try:
      logger.info(f"Handling call action: {action}")

      if action == "transfer":
        return await self._handle_transfer(params or {})
      elif action == "hold":
        return await self._handle_hold(params or {})
      elif action == "mute":
        return await self._handle_mute(params or {})
      elif action == "end_call":
        return await self._handle_end_call(params or {})
      else:
        return AgentResponse(
            text=f"I'm not sure how to perform the action: {action}",
            confidence=0.3
        )

    except Exception as e:
      logger.error(f"Error handling call action {action}: {str(e)}")
      return AgentResponse(
          text="I encountered an issue while trying to perform that action.",
          confidence=0.0
      )

  async def _handle_transfer(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle call transfer action."""
    target = params.get("target", "operator")
    return AgentResponse(
        text=f"I'll transfer you to {target} now. Please hold for a moment.",
        action="transfer",
        metadata=params
    )

  async def _handle_hold(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle call hold action."""
    return AgentResponse(
        text="I'll put you on hold for a moment. Please wait.",
        action="hold",
        metadata=params
    )

  async def _handle_mute(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle call mute action."""
    return AgentResponse(
        text="I'll mute the call now.",
        action="mute",
        metadata=params
    )

  async def _handle_end_call(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle end call action."""
    return AgentResponse(
        text="Thank you for calling. Have a great day!",
        action="end_call",
        metadata=params
    )
