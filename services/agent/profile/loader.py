"""
Agent profile loader service
"""
from typing import Optional, Dict, Any
from data.db.models.agentconfig import AgentConfig
from data.db.ops.agent.config import AgentConfigOps
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AgentProfileLoader:
  """Service for loading and managing agent profiles"""

  def __init__(self):
    self.config_ops = AgentConfigOps()

  async def get_agent_config(self, agent_id: str) -> Optional[AgentConfig]:
    """
    Get agent configuration by ID

    Args:
        agent_id: The agent identifier

    Returns:
        AgentConfig object or None if not found
    """
    try:
      return await self.config_ops.get_by_id(agent_id)
    except Exception as e:
      logger.error(f"Error loading agent config {agent_id}: {e}")
      return None

  async def create_agent_config(self, config_data: Dict[str, Any]) -> Optional[AgentConfig]:
    """
    Create new agent configuration

    Args:
        config_data: Configuration data

    Returns:
        Created AgentConfig object or None if failed
    """
    try:
      return await self.config_ops.create(config_data)
    except Exception as e:
      logger.error(f"Error creating agent config: {e}")
      return None

  async def update_agent_config(self, agent_id: str, config_data: Dict[str, Any]) -> Optional[AgentConfig]:
    """
    Update agent configuration

    Args:
        agent_id: The agent identifier
        config_data: Updated configuration data

    Returns:
        Updated AgentConfig object or None if failed
    """
    try:
      return await self.config_ops.update(agent_id, config_data)
    except Exception as e:
      logger.error(f"Error updating agent config {agent_id}: {e}")
      return None

  async def delete_agent_config(self, agent_id: str) -> bool:
    """
    Delete agent configuration

    Args:
        agent_id: The agent identifier

    Returns:
        True if deleted successfully, False otherwise
    """
    try:
      return await self.config_ops.delete(agent_id)
    except Exception as e:
      logger.error(f"Error deleting agent config {agent_id}: {e}")
      return False
