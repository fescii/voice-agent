"""
Delete agent memory from PostgreSQL database.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from data.db.models.memory import AgentMemory
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def delete_agent_memory(
    session: AsyncSession,
    agent_id: str,
    conversation_id: str
) -> bool:
  """
  Delete agent memory from the database.

  Args:
      session: Database session
      agent_id: ID of the agent
      conversation_id: ID of the conversation

  Returns:
      bool: Success status
  """
  try:
    stmt = delete(AgentMemory).where(
        AgentMemory.agent_id == agent_id,
        AgentMemory.conversation_id == conversation_id
    )

    await session.execute(stmt)
    await session.commit()
    return True
  except Exception as e:
    logger.error(f"Error deleting agent memory: {e}")
    await session.rollback()
    return False
