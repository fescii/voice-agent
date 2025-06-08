"""
CRUD operations for agent memory.
"""
import json
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.dialects.postgresql import insert

from data.db.models.memory import AgentMemory
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def save_agent_memory(
    session: AsyncSession,
    agent_id: str,
    conversation_id: str,
    short_term: Dict[str, Any],
    long_term: Dict[str, Any],
    working_memory: Dict[str, Any]
) -> bool:
  """
  Save agent memory to the database.

  Args:
      session: Database session
      agent_id: ID of the agent
      conversation_id: ID of the conversation
      short_term: Short-term memory items
      long_term: Long-term memory items
      working_memory: Working memory data

  Returns:
      bool: Success status
  """
  try:
    # Use PostgreSQL's ON CONFLICT DO UPDATE (upsert)
    stmt = insert(AgentMemory).values(
        agent_id=agent_id,
        conversation_id=conversation_id,
        last_accessed=datetime.now(timezone.utc),
        short_term=short_term,
        long_term=long_term,
        working_memory=working_memory
    )

    # Handle conflict by updating existing record
    stmt = stmt.on_conflict_do_update(
        constraint=f"{AgentMemory.__tablename__}_agent_id_conversation_id_key",
        set_={
            "last_accessed": datetime.now(timezone.utc),
            "short_term": short_term,
            "long_term": long_term,
            "working_memory": working_memory
        }
    )

    await session.execute(stmt)
    await session.commit()
    return True
  except Exception as e:
    logger.error(f"Error saving agent memory: {e}")
    await session.rollback()
    return False


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
