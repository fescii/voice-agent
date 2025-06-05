"""
Save agent memory to PostgreSQL database.
"""
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
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
        last_accessed=datetime.utcnow(),
        short_term=short_term,
        long_term=long_term,
        working_memory=working_memory
    )

    # Handle conflict by updating existing record
    stmt = stmt.on_conflict_do_update(
        constraint=f"{AgentMemory.__tablename__}_agent_id_conversation_id_key",
        set_={
            "last_accessed": datetime.utcnow(),
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
