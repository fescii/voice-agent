"""
Action handling and delegation management.
"""
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from ...response import AgentResponse

logger = get_logger(__name__)


class ActionDelegator:
  """Handles action delegation to specialized handlers."""

  def __init__(self, agent_core):
    """Initialize the action delegator."""
    self.agent_core = agent_core

  async def handle_call_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> AgentResponse:
    """Handle call-specific actions (delegated to action handler)."""
    return await self.agent_core.action_handler.handle_call_action(action, params)

  async def get_conversation_summary(self) -> Dict[str, Any]:
    """Get conversation summary (delegated to conversation analyzer)."""
    return await self.agent_core.conversation_analyzer.get_conversation_summary()

  async def update_script(self, script_name: str, script_data: Optional[Dict[str, Any]] = None) -> bool:
    """Update agent script (delegated to script manager)."""
    return await self.agent_core.script_manager.update_script(script_name, script_data)

  def get_current_script(self) -> Optional[str]:
    """Get current script name."""
    return self.agent_core.script_manager.get_current_script()
