"""
Agent router service for managing agent assignments and routing
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from data.db.models.agentconfig import AgentConfig
from data.db.ops.agent.config import AgentConfigOps
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AgentRouter:
  """Service for routing calls to appropriate agents"""

  def __init__(self):
    self.config_ops = AgentConfigOps()

  async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current status of an agent

    Args:
        agent_id: The agent identifier

    Returns:
        Dictionary with agent status information
    """
    try:
      agent_config = await self.config_ops.get_by_id(agent_id)
      if not agent_config:
        return None

      # Calculate status based on current call count and availability
      status = "offline"
      if agent_config.is_active:
        if agent_config.current_call_count >= agent_config.max_concurrent_calls:
          status = "busy"
        else:
          status = "available"

      return {
          "agent_id": agent_config.agent_id,
          "name": agent_config.name,
          "active": agent_config.is_active,
          "current_calls": int(agent_config.current_call_count),
          "max_calls": int(agent_config.max_concurrent_calls),
          "status": status,
          "last_activity": agent_config.updated_at
      }
    except Exception as e:
      logger.error(f"Error getting agent status {agent_id}: {e}")
      return None

  async def get_all_agent_statuses(self) -> List[Dict[str, Any]]:
    """
    Get status of all agents

    Returns:
        List of agent status dictionaries
    """
    try:
      agent_configs = await self.config_ops.get_all()
      statuses = []

      for config in agent_configs:
        status_info = await self.get_agent_status(config.agent_id)
        if status_info:
          statuses.append(status_info)

      return statuses
    except Exception as e:
      logger.error(f"Error getting all agent statuses: {e}")
      return []

  async def find_available_agent(self, criteria: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Find an available agent for a new call

    Args:
        criteria: Optional criteria for agent selection

    Returns:
        Agent ID of available agent or None if none available
    """
    try:
      agent_configs = await self.config_ops.get_all()

      for config in agent_configs:
        if (config.is_active and
                config.current_call_count < config.max_concurrent_calls):
          return config.agent_id

      return None
    except Exception as e:
      logger.error(f"Error finding available agent: {e}")
      return None

  async def assign_call_to_agent(self, agent_id: str, call_id: str) -> bool:
    """
    Assign a call to an agent (increment call count)

    Args:
        agent_id: The agent identifier
        call_id: The call identifier

    Returns:
        True if assignment successful, False otherwise
    """
    try:
      agent_config = await self.config_ops.get_by_id(agent_id)
      if not agent_config:
        return False

      if agent_config.current_call_count >= agent_config.max_concurrent_calls:
        return False

      # Increment call count
      updated_data = {
          "current_call_count": agent_config.current_call_count + 1
      }

      result = await self.config_ops.update(agent_id, updated_data)
      return result is not None
    except Exception as e:
      logger.error(f"Error assigning call to agent {agent_id}: {e}")
      return False

  async def release_call_from_agent(self, agent_id: str, call_id: str) -> bool:
    """
    Release a call from an agent (decrement call count)

    Args:
        agent_id: The agent identifier
        call_id: The call identifier

    Returns:
        True if release successful, False otherwise
    """
    try:
      agent_config = await self.config_ops.get_by_id(agent_id)
      if not agent_config:
        return False

      # Decrement call count (ensure it doesn't go below 0)
      new_count = max(0, agent_config.current_call_count - 1)
      updated_data = {
          "current_call_count": new_count
      }

      result = await self.config_ops.update(agent_id, updated_data)
      return result is not None
    except Exception as e:
      logger.error(f"Error releasing call from agent {agent_id}: {e}")
      return False
