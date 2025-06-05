"""
Persistent storage operations for agent memory.

This implementation uses PostgreSQL database for persistent storage.
"""
import json
from typing import Optional, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

from core.logging.setup import get_logger
from data.db.connection import get_db_session
from data.db.ops.memory import (
    save_agent_memory,
    get_agent_memory,
    delete_agent_memory
)
from ..models.item import MemoryItem, ConversationMemory

logger = get_logger(__name__)


class MemoryStorage:
  """Handles persistent storage of agent memory."""

  def __init__(self, agent_id: str):
    """Initialize storage with agent ID."""
    self.agent_id = agent_id

  async def load_conversation_memory(self, conversation_id: str) -> Optional[ConversationMemory]:
    """Load conversation memory from PostgreSQL database."""
    try:
      async with get_db_session() as session:
        memory_data = await get_agent_memory(session, self.agent_id, conversation_id)

        if not memory_data:
          return None

        # Reconstruct memory objects
        memory = ConversationMemory(conversation_id=conversation_id)

        # Reconstruct short-term memory
        if "short_term" in memory_data:
          for key, item_data in memory_data["short_term"].items():
            memory.short_term[key] = MemoryItem(
                key=key,
                value=item_data["value"],
                timestamp=datetime.fromisoformat(item_data["timestamp"]),
                ttl=item_data.get("ttl"),
                importance=item_data.get("importance", 1.0),
                access_count=item_data.get("access_count", 0),
                tags=set(item_data.get("tags", []))
            )

        # Reconstruct long-term memory
        if "long_term" in memory_data:
          for key, item_data in memory_data["long_term"].items():
            memory.long_term[key] = MemoryItem(
                key=key,
                value=item_data["value"],
                timestamp=datetime.fromisoformat(item_data["timestamp"]),
                ttl=item_data.get("ttl"),
                importance=item_data.get("importance", 1.0),
                access_count=item_data.get("access_count", 0),
                tags=set(item_data.get("tags", []))
            )

        # Reconstruct working memory
        memory.working_memory = memory_data.get("working_memory", {})

        if "last_accessed" in memory_data:
          memory.last_accessed = datetime.fromisoformat(
              memory_data["last_accessed"])

        return memory

    except Exception as e:
      logger.warning(
          f"Error loading conversation memory from PostgreSQL: {str(e)}")
      return None

  async def persist_conversation_memory(self, conversation_id: str, memory: ConversationMemory):
    """Persist conversation memory to PostgreSQL database."""
    try:
      # Prepare memory data
      short_term_dict = {}
      long_term_dict = {}

      # Serialize short-term memory
      for key, memory_item in memory.short_term.items():
        short_term_dict[key] = {
            "value": memory_item.value,
            "timestamp": memory_item.timestamp.isoformat(),
            "ttl": memory_item.ttl,
            "importance": memory_item.importance,
            "access_count": memory_item.access_count,
            "tags": list(memory_item.tags)
        }

      # Serialize long-term memory
      for key, memory_item in memory.long_term.items():
        long_term_dict[key] = {
            "value": memory_item.value,
            "timestamp": memory_item.timestamp.isoformat(),
            "ttl": memory_item.ttl,
            "importance": memory_item.importance,
            "access_count": memory_item.access_count,
            "tags": list(memory_item.tags)
        }

      # Save to PostgreSQL database
      async with get_db_session() as session:
        success = await save_agent_memory(
            session,
            self.agent_id,
            conversation_id,
            short_term_dict,
            long_term_dict,
            memory.working_memory
        )

        if not success:
          logger.warning(
              f"Failed to save agent memory to PostgreSQL for conversation {conversation_id}")

    except Exception as e:
      logger.warning(
          f"Error persisting conversation memory to PostgreSQL: {str(e)}")

  async def delete_conversation_memory(self, conversation_id: str):
    """Delete conversation memory from PostgreSQL database."""
    try:
      async with get_db_session() as session:
        success = await delete_agent_memory(session, self.agent_id, conversation_id)
        if not success:
          logger.warning(
              f"Failed to delete agent memory from PostgreSQL for conversation {conversation_id}")
    except Exception as e:
      logger.warning(
          f"Error deleting conversation memory from PostgreSQL: {str(e)}")
