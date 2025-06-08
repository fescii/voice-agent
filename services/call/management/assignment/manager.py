"""
Agent assignment and load balancing.
"""

from typing import Dict, Optional, List
import asyncio
from core.logging.setup import get_logger
from services.ringover import CallInfo

logger = get_logger(__name__)


class AgentAssignmentManager:
  """Manages agent assignment and load balancing."""

  def __init__(self):
    """Initialize agent assignment manager."""
    self.agent_loads: Dict[str, int] = {}
    self.pending_calls: List[CallInfo] = []
    self.assignment_lock = asyncio.Lock()

  async def assign_agent(self, call_info: CallInfo) -> Optional[str]:
    """
    Assign an agent to a call using load balancing.

    Args:
        call_info: Information about the incoming call

    Returns:
        Agent ID if assignment successful, None otherwise
    """
    async with self.assignment_lock:
      # Find agent with lowest load
      available_agents = await self._get_available_agents()

      if not available_agents:
        logger.warning("No available agents for call assignment")
        self.pending_calls.append(call_info)
        return None

      # Simple load balancing - pick agent with lowest load
      best_agent = min(
          available_agents, key=lambda agent_id: self.agent_loads.get(agent_id, 0))

      # Increment load for assigned agent
      self.agent_loads[best_agent] = self.agent_loads.get(best_agent, 0) + 1

      logger.info(f"Assigned agent {best_agent} to call {call_info.call_id}")
      return best_agent

  async def release_agent(self, agent_id: str):
    """Release an agent from a call, decreasing their load."""
    if agent_id in self.agent_loads:
      self.agent_loads[agent_id] = max(0, self.agent_loads[agent_id] - 1)
      logger.info(
          f"Released agent {agent_id}, current load: {self.agent_loads[agent_id]}")

      # Check if there are pending calls that can be assigned
      await self._process_pending_calls()

  async def _get_available_agents(self) -> List[str]:
    """Get list of available agents."""
    # TODO: Integrate with actual agent availability system
    # For now, return some mock agents
    return ["agent_1", "agent_2", "agent_3"]

  async def _process_pending_calls(self):
    """Process any pending calls waiting for agent assignment."""
    if not self.pending_calls:
      return

    pending_call = self.pending_calls.pop(0)
    agent_id = await self.assign_agent(pending_call)

    if agent_id:
      # TODO: Trigger actual call handling for the assigned agent
      logger.info(
          f"Processed pending call {pending_call.call_id} with agent {agent_id}")

  async def get_agent_loads(self) -> Dict[str, int]:
    """Get current load for all agents."""
    return self.agent_loads.copy()

  async def set_agent_availability(self, agent_id: str, available: bool):
    """Set agent availability status."""
    # TODO: Implement agent availability management
    logger.info(f"Agent {agent_id} availability set to {available}")
