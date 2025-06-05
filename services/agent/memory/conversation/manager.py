"""
Conversation-specific memory management.
"""
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from core.logging.setup import get_logger
from ..models.item import MemoryItem, ConversationMemory
from ..storage.persistent import MemoryStorage

logger = get_logger(__name__)


class ConversationMemoryManager:
  """Manages memory for individual conversations."""

  def __init__(self, agent_id: str):
    """Initialize conversation memory manager."""
    self.agent_id = agent_id
    self.storage = MemoryStorage(agent_id)
    self.memory_limits = {
        "short_term_max": 100,
        "long_term_max": 500,
        "working_memory_max": 50
    }

  async def initialize_conversation_memory(self, conversation_id: str) -> ConversationMemory:
    """Initialize or load conversation memory."""
    try:
      # Try to load from persistence first
      memory = await self.storage.load_conversation_memory(conversation_id)

      if memory is None:
        # Create new conversation memory
        memory = ConversationMemory(conversation_id=conversation_id)
        logger.info(f"Created new conversation memory for: {conversation_id}")
      else:
        logger.info(
            f"Loaded existing conversation memory for: {conversation_id}")

      return memory

    except Exception as e:
      logger.error(f"Error initializing conversation memory: {str(e)}")
      raise

  async def store_memory(
      self,
      conversation_id: str,
      key: str,
      value: Any,
      memory_type: str = "short_term",
      ttl: Optional[int] = None,
      importance: float = 1.0,
      tags: Optional[Set[str]] = None
  ):
    """Store information in conversation memory."""
    try:
      memory = await self.initialize_conversation_memory(conversation_id)

      memory_item = MemoryItem(
          key=key,
          value=value,
          timestamp=datetime.now(),
          ttl=ttl,
          importance=importance,
          tags=tags or set()
      )

      if memory_type == "short_term":
        memory.short_term[key] = memory_item
        await self._enforce_memory_limits(memory.short_term, "short_term_max")
      elif memory_type == "long_term":
        memory.long_term[key] = memory_item
        await self._enforce_memory_limits(memory.long_term, "long_term_max")
      elif memory_type == "working":
        memory.working_memory[key] = value
        await self._enforce_working_memory_limits(memory.working_memory)

      memory.last_accessed = datetime.now()

      # Persist the updated memory
      await self.storage.persist_conversation_memory(conversation_id, memory)

      logger.debug(f"Stored memory: {key} in {memory_type}")

    except Exception as e:
      logger.error(f"Error storing memory: {str(e)}")
      raise

  async def retrieve_memory(
      self,
      conversation_id: str,
      key: str,
      memory_type: str = "short_term"
  ) -> Optional[Any]:
    """Retrieve information from conversation memory."""
    try:
      memory = await self.initialize_conversation_memory(conversation_id)

      # Search in specified memory type
      if memory_type == "short_term":
        memory_item = memory.short_term.get(key)
      elif memory_type == "long_term":
        memory_item = memory.long_term.get(key)
      elif memory_type == "working":
        return memory.working_memory.get(key)
      else:
        memory_item = None

      if memory_item:
        # Check TTL
        if memory_item.ttl:
          age = (datetime.now() - memory_item.timestamp).total_seconds()
          if age > memory_item.ttl:
            # Remove expired item
            await self.delete_memory(conversation_id, key, memory_type)
            return None

        # Update access count
        memory_item.access_count += 1
        memory.last_accessed = datetime.now()

        logger.debug(f"Retrieved memory: {key} from {memory_type}")
        return memory_item.value

      return None

    except Exception as e:
      logger.error(f"Error retrieving memory: {str(e)}")
      return None

  async def delete_memory(
      self,
      conversation_id: str,
      key: str,
      memory_type: str = "short_term"
  ) -> bool:
    """Delete specific memory item."""
    try:
      memory = await self.initialize_conversation_memory(conversation_id)

      if memory_type == "short_term" and key in memory.short_term:
        del memory.short_term[key]
      elif memory_type == "long_term" and key in memory.long_term:
        del memory.long_term[key]
      elif memory_type == "working" and key in memory.working_memory:
        del memory.working_memory[key]
      else:
        return False

      # Persist the updated memory
      await self.storage.persist_conversation_memory(conversation_id, memory)

      logger.debug(f"Deleted memory: {key} from {memory_type}")
      return True

    except Exception as e:
      logger.error(f"Error deleting memory: {str(e)}")
      return False

  async def _enforce_memory_limits(self, memory_dict: Dict[str, MemoryItem], limit_key: str):
    """Enforce memory limits by removing least important items."""
    limit = self.memory_limits.get(limit_key, 100)

    if len(memory_dict) > limit:
      # Sort by importance score (ascending) and access count
      items_to_remove = sorted(
          memory_dict.items(),
          key=lambda x: (x[1].importance, x[1].access_count)
      )[:len(memory_dict) - limit]

      for key, _ in items_to_remove:
        del memory_dict[key]

  async def _enforce_working_memory_limits(self, working_memory: Dict[str, Any]):
    """Enforce working memory limits."""
    limit = self.memory_limits.get("working_memory_max", 50)

    if len(working_memory) > limit:
      # Remove oldest items (simple FIFO)
      items_to_remove = len(working_memory) - limit
      keys_to_remove = list(working_memory.keys())[:items_to_remove]

      for key in keys_to_remove:
        del working_memory[key]
