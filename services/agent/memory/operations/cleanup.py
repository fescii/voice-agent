"""
Memory cleanup operations.
"""
from typing import Dict, List
from datetime import datetime
from core.logging.setup import get_logger
from data.redis.ops.session.delete import delete_session_data
from ..models.item import ConversationMemory

logger = get_logger(__name__)


class MemoryCleanupManager:
  """Handles memory cleanup operations."""

  def __init__(self, agent_id: str):
    """Initialize cleanup manager."""
    self.agent_id = agent_id

  async def cleanup_old_conversations(
      self,
      conversations: Dict[str, ConversationMemory],
      max_age_hours: int = 24
  ) -> List[str]:
    """
    Clean up old conversation memories.

    Args:
        conversations: Dictionary of conversation memories
        max_age_hours: Maximum age in hours before cleanup

    Returns:
        List of cleaned up conversation IDs
    """
    try:
      current_time = datetime.now()
      conversations_to_remove = []

      for conversation_id, memory in conversations.items():
        age = current_time - memory.last_accessed
        if age.total_seconds() > max_age_hours * 3600:
          conversations_to_remove.append(conversation_id)

      # Remove from persistence
      for conversation_id in conversations_to_remove:
        memory_key = f"agent_memory:{self.agent_id}:{conversation_id}"
        await delete_session_data(memory_key)

      if conversations_to_remove:
        logger.info(
            f"Cleaned up {len(conversations_to_remove)} old conversations")

      return conversations_to_remove

    except Exception as e:
      logger.error(f"Error cleaning up old conversations: {str(e)}")
      return []

  async def cleanup_expired_memories(self, memory: ConversationMemory):
    """Clean up expired memory items."""
    try:
      current_time = datetime.now()
      expired_keys = []

      # Check short-term memory
      for key, memory_item in memory.short_term.items():
        if memory_item.ttl:
          age = (current_time - memory_item.timestamp).total_seconds()
          if age > memory_item.ttl:
            expired_keys.append(("short_term", key))

      # Check long-term memory
      for key, memory_item in memory.long_term.items():
        if memory_item.ttl:
          age = (current_time - memory_item.timestamp).total_seconds()
          if age > memory_item.ttl:
            expired_keys.append(("long_term", key))

      # Remove expired items
      for memory_type, key in expired_keys:
        if memory_type == "short_term":
          del memory.short_term[key]
        elif memory_type == "long_term":
          del memory.long_term[key]

      if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} expired memories")

    except Exception as e:
      logger.warning(f"Error cleaning up expired memories: {str(e)}")

  async def cleanup_low_value_memories(
      self,
      memory: ConversationMemory,
      importance_threshold: float = 0.1,
      max_age_hours: int = 24
  ):
    """Clean up low-value, unused memories."""
    try:
      current_time = datetime.now()
      keys_to_remove = []

      # Check short-term memory for low-value items
      for key, memory_item in memory.short_term.items():
        if (memory_item.importance < importance_threshold and
                memory_item.access_count == 0):
          age = (current_time - memory_item.timestamp).total_seconds()
          if age > max_age_hours * 3600:
            keys_to_remove.append(key)

      # Remove low-value items
      for key in keys_to_remove:
        del memory.short_term[key]

      if keys_to_remove:
        logger.debug(f"Cleaned up {len(keys_to_remove)} low-value memories")

    except Exception as e:
      logger.warning(f"Error cleaning up low-value memories: {str(e)}")
