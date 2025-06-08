"""
Agent configuration database operations
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from datetime import datetime, timezone

from data.db.models.agentconfig import AgentConfig
from data.db.connection import get_db_session
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AgentConfigOps:
  """Database operations for agent configurations"""

  async def get_by_id(self, agent_id: str) -> Optional[AgentConfig]:
    """
    Get agent configuration by ID

    Args:
        agent_id: The agent identifier

    Returns:
        AgentConfig object or None if not found
    """
    async with get_db_session() as session:
      try:
        stmt = select(AgentConfig).where(AgentConfig.agent_id == agent_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
      except Exception as e:
        logger.error(f"Error fetching agent config {agent_id}: {e}")
        return None

  async def get_all(self) -> List[AgentConfig]:
    """
    Get all agent configurations

    Returns:
        List of AgentConfig objects
    """
    async with get_db_session() as session:
      try:
        stmt = select(AgentConfig)
        result = await session.execute(stmt)
        return list(result.scalars().all())
      except Exception as e:
        logger.error(f"Error fetching all agent configs: {e}")
        return []

  async def create(self, config_data: Dict[str, Any]) -> Optional[AgentConfig]:
    """
    Create new agent configuration

    Args:
        config_data: Configuration data

    Returns:
        Created AgentConfig object or None if failed
    """
    async with get_db_session() as session:
      try:
        # Generate agent_id if not provided
        if 'agent_id' not in config_data:
          import uuid
          config_data['agent_id'] = str(uuid.uuid4())

        config = AgentConfig(**config_data)
        session.add(config)
        await session.commit()
        await session.refresh(config)
        return config
      except Exception as e:
        logger.error(f"Error creating agent config: {e}")
        await session.rollback()
        return None

  async def update(self, agent_id: str, config_data: Dict[str, Any]) -> Optional[AgentConfig]:
    """
    Update agent configuration

    Args:
        agent_id: The agent identifier
        config_data: Updated configuration data

    Returns:
        Updated AgentConfig object or None if failed
    """
    async with get_db_session() as session:
      try:
        # Update timestamp
        config_data['updated_at'] = datetime.now(timezone.utc)

        stmt = (
            update(AgentConfig)
            .where(AgentConfig.agent_id == agent_id)
            .values(**config_data)
            .returning(AgentConfig)
        )
        result = await session.execute(stmt)
        await session.commit()
        return result.scalar_one_or_none()
      except Exception as e:
        logger.error(f"Error updating agent config {agent_id}: {e}")
        await session.rollback()
        return None

  async def delete(self, agent_id: str) -> bool:
    """
    Delete agent configuration

    Args:
        agent_id: The agent identifier

    Returns:
        True if deleted successfully, False otherwise
    """
    async with get_db_session() as session:
      try:
        stmt = delete(AgentConfig).where(AgentConfig.agent_id == agent_id)
        result = await session.execute(stmt)
        await session.commit()
        return result.rowcount > 0
      except Exception as e:
        logger.error(f"Error deleting agent config {agent_id}: {e}")
        await session.rollback()
        return False
