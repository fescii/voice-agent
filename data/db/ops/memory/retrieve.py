"""
Retrieve agent memory from PostgreSQL database.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from data.db.models.memory import AgentMemory
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_agent_memory(
    session: AsyncSession,
    agent_id: str,
    conversation_id: str
) -> Optional[Dict[str, Any]]:
  """
  Retrieve agent memory from the database.

  Args:
      session: Database session
      agent_id: ID of the agent
      conversation_id: ID of the conversation

  Returns:
      Optional[Dict[str, Any]]: Memory data or None if not found
  """
  try:
    stmt = select(AgentMemory).where(
        AgentMemory.agent_id == agent_id,
        AgentMemory.conversation_id == conversation_id
    )

    result = await session.execute(stmt)
    memory = result.scalars().first()

    if memory:
      # Update last_accessed timestamp
      update_stmt = update(AgentMemory).where(
          AgentMemory.id == memory.id
      ).values(
          last_accessed=datetime.now(timezone.utc)
      )
      await session.execute(update_stmt)
      await session.commit()

      # Return memory data
      return {
          "conversation_id": memory.conversation_id,
          "short_term": memory.short_term,
          "long_term": memory.long_term,
          "working_memory": memory.working_memory,
          "last_accessed": memory.last_accessed.isoformat()
      }

    return None
  except Exception as e:
    logger.error(f"Error retrieving agent memory: {e}")
    return None
