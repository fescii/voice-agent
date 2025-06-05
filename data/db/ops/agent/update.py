"""
Update operations for agent configs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any
from datetime import datetime

from ...models.agentconfig import AgentConfig
from ....core.logging import get_logger

logger = get_logger(__name__)


async def update_agent_config(
    session: AsyncSession,
    agent_id: str,
    **kwargs
) -> bool:
  """
  Update agent configuration.

  Args:
      session: Database session
      agent_id: Agent identifier
      **kwargs: Fields to update

  Returns:
      True if update was successful
  """
  try:
    if not kwargs:
      return True

    update_data = {**kwargs, "updated_at": datetime.utcnow()}

    result = await session.execute(
        update(AgentConfig)
        .where(AgentConfig.agent_id == agent_id)
        .values(**update_data)
    )

    await session.commit()

    if result.rowcount > 0:
      logger.info(f"Updated agent config {agent_id}")
      return True
    else:
      logger.warning(f"No agent found with ID {agent_id} to update")
      return False

  except SQLAlchemyError as e:
    logger.error(f"Failed to update agent config {agent_id}: {e}")
    await session.rollback()
    return False


async def update_agent_call_count(
    session: AsyncSession,
    agent_id: str,
    increment: int = 1
) -> bool:
  """
  Update agent's current call count.

  Args:
      session: Database session
      agent_id: Agent identifier
      increment: Amount to change call count (can be negative)

  Returns:
      True if update was successful
  """
  try:
    # Get current count first
    agent = await session.get(AgentConfig, agent_id)
    if not agent:
      logger.warning(f"No agent found with ID {agent_id}")
      return False

    new_count = max(0, agent.current_call_count + increment)

    result = await session.execute(
        update(AgentConfig)
        .where(AgentConfig.agent_id == agent_id)
        .values(
            current_call_count=new_count,
            updated_at=datetime.utcnow()
        )
    )

    await session.commit()

    if result.rowcount > 0:
      logger.info(f"Updated agent {agent_id} call count to {new_count}")
      return True
    else:
      return False

  except SQLAlchemyError as e:
    logger.error(f"Failed to update agent call count {agent_id}: {e}")
    await session.rollback()
    return False
