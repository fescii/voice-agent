"""
Persistent storage operations for agent memory.
"""
import json
from typing import Optional
from datetime import datetime
from core.logging.setup import get_logger
from data.redis.ops.session.store import store_call_session
from data.redis.ops.session.retrieve import get_call_session
from data.redis.ops.session.delete import delete_session_data
from ..models.item import MemoryItem, ConversationMemory

logger = get_logger(__name__)


class MemoryStorage:
  """Handles persistent storage of agent memory."""

  def __init__(self, agent_id: str):
    """Initialize storage with agent ID."""
    self.agent_id = agent_id

  async def load_conversation_memory(self, conversation_id: str) -> Optional[ConversationMemory]:
    """Load conversation memory from persistence."""
    try:
      memory_key = f"agent_memory:{self.agent_id}:{conversation_id}"
      memory_data = await get_call_session(memory_key)

      if memory_data:
        # Memory data is already a dictionary from get_call_session
        memory_dict = memory_data

        # Reconstruct memory objects
        memory = ConversationMemory(conversation_id=conversation_id)

        # Reconstruct short-term memory
        if "short_term" in memory_dict:
          for key, item_data in memory_dict["short_term"].items():
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
        if "long_term" in memory_dict:
          for key, item_data in memory_dict["long_term"].items():
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
        memory.working_memory = memory_dict.get("working_memory", {})

        if "last_accessed" in memory_dict:
          memory.last_accessed = datetime.fromisoformat(
              memory_dict["last_accessed"])

        return memory

      return None

    except Exception as e:
      logger.warning(f"Error loading conversation memory: {str(e)}")
      return None

  async def persist_conversation_memory(self, conversation_id: str, memory: ConversationMemory):
    """Persist conversation memory to storage."""
    try:
      memory_key = f"agent_memory:{self.agent_id}:{conversation_id}"

      # Serialize memory data
      memory_dict = {
          "conversation_id": conversation_id,
          "short_term": {},
          "long_term": {},
          "working_memory": memory.working_memory,
          "last_accessed": memory.last_accessed.isoformat()
      }

      # Serialize short-term memory
      for key, memory_item in memory.short_term.items():
        memory_dict["short_term"][key] = {
            "value": memory_item.value,
            "timestamp": memory_item.timestamp.isoformat(),
            "ttl": memory_item.ttl,
            "importance": memory_item.importance,
            "access_count": memory_item.access_count,
            "tags": list(memory_item.tags)
        }

      # Serialize long-term memory
      for key, memory_item in memory.long_term.items():
        memory_dict["long_term"][key] = {
            "value": memory_item.value,
            "timestamp": memory_item.timestamp.isoformat(),
            "ttl": memory_item.ttl,
            "importance": memory_item.importance,
            "access_count": memory_item.access_count,
            "tags": list(memory_item.tags)
        }

      memory_json = json.dumps(memory_dict, default=str)

      # Store with TTL (24 hours)
      await store_call_session(memory_key, memory_json, 24 * 3600)

    except Exception as e:
      logger.warning(f"Error persisting conversation memory: {str(e)}")

  async def delete_conversation_memory(self, conversation_id: str):
    """Delete conversation memory from storage."""
    try:
      memory_key = f"agent_memory:{self.agent_id}:{conversation_id}"
      await delete_session_data(memory_key)
    except Exception as e:
      logger.warning(f"Error deleting conversation memory: {str(e)}")
