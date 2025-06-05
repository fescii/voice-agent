"""
Read operations for agent configs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from data.db.models.agentconfig import AgentConfig
from core.logging import get_logger

logger = get_logger(__name__)


async def get_agent_config(
    session: AsyncSession,
    agent_id: str
) -> Optional[AgentConfig]:
  """
  Get agent configuration by agent ID.

  Args:
      session: Database session
      agent_id: Agent identifier

  Returns:
      AgentConfig instance or None if not found
  """
  try:
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.agent_id == agent_id)
    )
    return result.scalar_one_or_none()

  except SQLAlchemyError as e:
    logger.error(f"Failed to get agent config {agent_id}: {e}")
    return None


async def get_active_agents(session: AsyncSession) -> List[AgentConfig]:
  """
  Get all active agent configurations.

  Args:
      session: Database session

  Returns:
      List of active AgentConfig instances
  """
  try:
    result = await session.execute(
        select(AgentConfig)
        .where(AgentConfig.is_active == True)
        .order_by(AgentConfig.name)
    )
    return list(result.scalars().all())

  except SQLAlchemyError as e:
    logger.error(f"Failed to get active agents: {e}")
    return []


async def get_all_agents(session: AsyncSession) -> List[AgentConfig]:
  """
  Get all agent configurations.

  Args:
      session: Database session

  Returns:
      List of all AgentConfig instances
  """
  try:
    result = await session.execute(
        select(AgentConfig).order_by(AgentConfig.name)
    )
    return list(result.scalars().all())

  except SQLAlchemyError as e:
    logger.error(f"Failed to get all agents: {e}")
    return []
