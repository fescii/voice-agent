"""
Memory management for agent conversations and context.
"""

import asyncio
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import hashlib

from core.logging.setup import get_logger
from data.redis.ops.session.store import store_session_data
from data.redis.ops.session.retrieve import get_session_data
from data.redis.ops.session.delete import delete_session_data

logger = get_logger(__name__)


@dataclass
class MemoryItem:
  """Individual memory item."""
  key: str
  value: Any
  timestamp: datetime
  ttl: Optional[int] = None  # Time to live in seconds
  importance: float = 1.0    # Importance score (0.0 to 1.0)
  access_count: int = 0
  tags: Set[str] = field(default_factory=set)


@dataclass
class ConversationMemory:
  """Memory for a specific conversation."""
  conversation_id: str
  short_term: Dict[str, MemoryItem] = field(default_factory=dict)
  long_term: Dict[str, MemoryItem] = field(default_factory=dict)
  working_memory: Dict[str, Any] = field(default_factory=dict)
  last_accessed: datetime = field(default_factory=datetime.now)


class MemoryManager:
  """Manages agent memory across conversations."""

  def __init__(self, agent_id: str):
    """Initialize memory manager."""
    self.agent_id = agent_id
    self.conversations: Dict[str, ConversationMemory] = {}
    self.global_memory: Dict[str, MemoryItem] = {}
    self.memory_limits = {
        "short_term_max": 100,      # Max items in short-term memory
        "long_term_max": 1000,      # Max items in long-term memory
        "working_memory_max": 20,   # Max items in working memory
        "global_memory_max": 5000   # Max items in global memory
    }
    self.cleanup_interval = 3600  # Cleanup every hour
    self._last_cleanup = datetime.now()

  async def initialize_conversation_memory(self, conversation_id: str) -> ConversationMemory:
    """
    Initialize memory for a new conversation.

    Args:
        conversation_id: Unique conversation identifier

    Returns:
        Conversation memory instance
    """
    try:
      logger.info(f"Initializing memory for conversation: {conversation_id}")

      # Load existing memory if available
      existing_memory = await self._load_conversation_memory(conversation_id)

      if existing_memory:
        self.conversations[conversation_id] = existing_memory
        logger.info(
            f"Loaded existing memory for conversation: {conversation_id}")
      else:
        # Create new conversation memory
        self.conversations[conversation_id] = ConversationMemory(
            conversation_id=conversation_id
        )
        logger.info(f"Created new memory for conversation: {conversation_id}")

      return self.conversations[conversation_id]

    except Exception as e:
      logger.error(f"Error initializing conversation memory: {str(e)}")
      raise

  async def store_memory(
      self,
      conversation_id: str,
      key: str,
      value: Any,
      memory_type: str = "short_term",
      importance: float = 1.0,
      ttl: Optional[int] = None,
      tags: Optional[Set[str]] = None
  ):
    """
    Store information in memory.

    Args:
        conversation_id: Conversation identifier
        key: Memory key
        value: Value to store
        memory_type: Type of memory (short_term, long_term, working)
        importance: Importance score (0.0 to 1.0)
        ttl: Time to live in seconds
        tags: Optional tags for categorization
    """
    try:
      if conversation_id not in self.conversations:
        await self.initialize_conversation_memory(conversation_id)

      memory = self.conversations[conversation_id]

      # Create memory item
      memory_item = MemoryItem(
          key=key,
          value=value,
          timestamp=datetime.now(),
          ttl=ttl,
          importance=importance,
          tags=tags or set()
      )

      # Store in appropriate memory type
      if memory_type == "short_term":
        memory.short_term[key] = memory_item
        await self._enforce_memory_limits(memory.short_term, "short_term_max")
      elif memory_type == "long_term":
        memory.long_term[key] = memory_item
        await self._enforce_memory_limits(memory.long_term, "long_term_max")
      elif memory_type == "working":
        memory.working_memory[key] = value
        await self._enforce_working_memory_limits(memory.working_memory)

      # Update last accessed time
      memory.last_accessed = datetime.now()

      # Persist to Redis
      await self._persist_conversation_memory(conversation_id, memory)

      logger.debug(f"Stored memory: {key} -> {memory_type}")

    except Exception as e:
      logger.error(f"Error storing memory: {str(e)}")
      raise

  async def retrieve_memory(
      self,
      conversation_id: str,
      key: str,
      memory_type: str = "short_term"
  ) -> Optional[Any]:
    """
    Retrieve information from memory.

    Args:
        conversation_id: Conversation identifier
        key: Memory key
        memory_type: Type of memory to search

    Returns:
        Retrieved value or None
    """
    try:
      if conversation_id not in self.conversations:
        await self.initialize_conversation_memory(conversation_id)

      memory = self.conversations[conversation_id]

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

  async def search_memory(
      self,
      conversation_id: str,
      query: str,
      memory_types: Optional[List[str]] = None,
      tags: Optional[Set[str]] = None
  ) -> List[Dict[str, Any]]:
    """
    Search memory by query and tags.

    Args:
        conversation_id: Conversation identifier
        query: Search query
        memory_types: Types of memory to search
        tags: Tags to filter by

    Returns:
        List of matching memory items
    """
    try:
      if conversation_id not in self.conversations:
        return []

      memory = self.conversations[conversation_id]
      memory_types = memory_types or ["short_term", "long_term"]
      results = []

      # Search in specified memory types
      for memory_type in memory_types:
        if memory_type == "short_term":
          items = memory.short_term
        elif memory_type == "long_term":
          items = memory.long_term
        else:
          continue

        for key, memory_item in items.items():
          # Check TTL
          if memory_item.ttl:
            age = (datetime.now() - memory_item.timestamp).total_seconds()
            if age > memory_item.ttl:
              continue

          # Query matching
          query_match = (
              query.lower() in key.lower() or
              query.lower() in str(memory_item.value).lower()
          )

          # Tag matching
          tag_match = not tags or tags.intersection(memory_item.tags)

          if query_match and tag_match:
            results.append({
                "key": key,
                "value": memory_item.value,
                "memory_type": memory_type,
                "timestamp": memory_item.timestamp,
                "importance": memory_item.importance,
                "access_count": memory_item.access_count,
                "tags": list(memory_item.tags)
            })

      # Sort by importance and recency
      results.sort(key=lambda x: (
          x["importance"], x["timestamp"]), reverse=True)

      logger.debug(f"Found {len(results)} memory items for query: {query}")
      return results

    except Exception as e:
      logger.error(f"Error searching memory: {str(e)}")
      return []

  async def delete_memory(
      self,
      conversation_id: str,
      key: str,
      memory_type: str = "short_term"
  ):
    """
    Delete information from memory.

    Args:
        conversation_id: Conversation identifier
        key: Memory key
        memory_type: Type of memory
    """
    try:
      if conversation_id not in self.conversations:
        return

      memory = self.conversations[conversation_id]

      if memory_type == "short_term" and key in memory.short_term:
        del memory.short_term[key]
      elif memory_type == "long_term" and key in memory.long_term:
        del memory.long_term[key]
      elif memory_type == "working" and key in memory.working_memory:
        del memory.working_memory[key]

      # Update persistence
      await self._persist_conversation_memory(conversation_id, memory)

      logger.debug(f"Deleted memory: {key} from {memory_type}")

    except Exception as e:
      logger.error(f"Error deleting memory: {str(e)}")

  async def promote_to_long_term(
      self,
      conversation_id: str,
      key: str,
      importance_threshold: float = 0.7
  ):
    """
    Promote short-term memory to long-term based on importance.

    Args:
        conversation_id: Conversation identifier
        key: Memory key
        importance_threshold: Minimum importance for promotion
    """
    try:
      if conversation_id not in self.conversations:
        return

      memory = self.conversations[conversation_id]

      if key in memory.short_term:
        memory_item = memory.short_term[key]

        # Check importance and access count
        if (memory_item.importance >= importance_threshold or
                memory_item.access_count >= 3):

          # Move to long-term memory
          memory.long_term[key] = memory_item
          del memory.short_term[key]

          logger.info(f"Promoted memory to long-term: {key}")

          # Update persistence
          await self._persist_conversation_memory(conversation_id, memory)

    except Exception as e:
      logger.error(f"Error promoting memory: {str(e)}")

  async def consolidate_memories(self, conversation_id: str):
    """
    Consolidate and optimize memory for a conversation.

    Args:
        conversation_id: Conversation identifier
    """
    try:
      if conversation_id not in self.conversations:
        return

      memory = self.conversations[conversation_id]

      # Promote frequently accessed items
      for key, memory_item in list(memory.short_term.items()):
        if memory_item.access_count >= 3 or memory_item.importance >= 0.8:
          await self.promote_to_long_term(conversation_id, key)

      # Remove low-importance, unused items
      await self._cleanup_unused_memories(memory)

      # Merge similar memories
      await self._merge_similar_memories(memory)

      logger.info(f"Consolidated memory for conversation: {conversation_id}")

    except Exception as e:
      logger.error(f"Error consolidating memories: {str(e)}")

  async def _enforce_memory_limits(self, memory_dict: Dict[str, MemoryItem], limit_key: str):
    """Enforce memory limits by removing least important items."""
    try:
      max_items = self.memory_limits[limit_key]

      if len(memory_dict) > max_items:
        # Sort by importance and access patterns
        items = list(memory_dict.items())
        items.sort(key=lambda x: (x[1].importance,
                   x[1].access_count, x[1].timestamp))

        # Remove least important items
        items_to_remove = items[:len(items) - max_items]
        for key, _ in items_to_remove:
          del memory_dict[key]

        logger.debug(
            f"Removed {len(items_to_remove)} items to enforce {limit_key}")

    except Exception as e:
      logger.warning(f"Error enforcing memory limits: {str(e)}")

  async def _enforce_working_memory_limits(self, working_memory: Dict[str, Any]):
    """Enforce working memory limits."""
    try:
      max_items = self.memory_limits["working_memory_max"]

      if len(working_memory) > max_items:
        # Remove oldest items (FIFO)
        items_to_remove = list(working_memory.keys())[
            :len(working_memory) - max_items]
        for key in items_to_remove:
          del working_memory[key]

        logger.debug(
            f"Removed {len(items_to_remove)} items from working memory")

    except Exception as e:
      logger.warning(f"Error enforcing working memory limits: {str(e)}")

  async def _cleanup_unused_memories(self, memory: ConversationMemory):
    """Clean up unused or expired memories."""
    try:
      current_time = datetime.now()

      # Clean up expired short-term memories
      expired_keys = []
      for key, memory_item in memory.short_term.items():
        if memory_item.ttl:
          age = (current_time - memory_item.timestamp).total_seconds()
          if age > memory_item.ttl:
            expired_keys.append(key)
        # Also remove very low importance, unaccessed items
        elif memory_item.importance < 0.1 and memory_item.access_count == 0:
          age = (current_time - memory_item.timestamp).total_seconds()
          if age > 3600:  # 1 hour
            expired_keys.append(key)

      for key in expired_keys:
        del memory.short_term[key]

      if expired_keys:
        logger.debug(f"Cleaned up {len(expired_keys)} unused memories")

    except Exception as e:
      logger.warning(f"Error cleaning up memories: {str(e)}")

  async def _merge_similar_memories(self, memory: ConversationMemory):
    """Merge similar memory items to optimize storage."""
    try:
      # Simple implementation - could be enhanced with semantic similarity
      merged_count = 0

      # Group by similar keys
      key_groups = {}
      for key in memory.short_term.keys():
        base_key = key.split("_")[0]  # Simple grouping by prefix
        if base_key not in key_groups:
          key_groups[base_key] = []
        key_groups[base_key].append(key)

      # Merge groups with multiple items
      for base_key, keys in key_groups.items():
        if len(keys) > 1:
          # Merge into most important item
          items = [(key, memory.short_term[key]) for key in keys]
          items.sort(key=lambda x: x[1].importance, reverse=True)

          main_key, main_item = items[0]

          # Merge values and metadata
          for key, item in items[1:]:
            if isinstance(main_item.value, list) and isinstance(item.value, list):
              main_item.value.extend(item.value)
            main_item.tags.update(item.tags)
            main_item.access_count += item.access_count

            # Remove merged item
            del memory.short_term[key]
            merged_count += 1

      if merged_count > 0:
        logger.debug(f"Merged {merged_count} similar memories")

    except Exception as e:
      logger.warning(f"Error merging memories: {str(e)}")

  async def _load_conversation_memory(self, conversation_id: str) -> Optional[ConversationMemory]:
    """Load conversation memory from persistence."""
    try:
      memory_key = f"agent_memory:{self.agent_id}:{conversation_id}"

      memory_data = await get_session_data(memory_key)

      if memory_data:
        # Deserialize memory data
        memory_dict = json.loads(memory_data)

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

  async def _persist_conversation_memory(self, conversation_id: str, memory: ConversationMemory):
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
      await store_session_data(memory_key, memory_json, 24 * 3600)

    except Exception as e:
      logger.warning(f"Error persisting conversation memory: {str(e)}")

  async def cleanup_old_conversations(self, max_age_hours: int = 24):
    """Clean up old conversation memories."""
    try:
      current_time = datetime.now()
      conversations_to_remove = []

      for conversation_id, memory in self.conversations.items():
        age = current_time - memory.last_accessed
        if age.total_seconds() > max_age_hours * 3600:
          conversations_to_remove.append(conversation_id)

      for conversation_id in conversations_to_remove:
        del self.conversations[conversation_id]

        # Also remove from persistence
        memory_key = f"agent_memory:{self.agent_id}:{conversation_id}"
        await delete_session_data(memory_key)

      if conversations_to_remove:
        logger.info(
            f"Cleaned up {len(conversations_to_remove)} old conversations")

    except Exception as e:
      logger.error(f"Error cleaning up old conversations: {str(e)}")

  async def get_memory_stats(self, conversation_id: str) -> Dict[str, Any]:
    """Get memory statistics for a conversation."""
    try:
      if conversation_id not in self.conversations:
        return {"error": "Conversation not found"}

      memory = self.conversations[conversation_id]

      return {
          "conversation_id": conversation_id,
          "short_term_count": len(memory.short_term),
          "long_term_count": len(memory.long_term),
          "working_memory_count": len(memory.working_memory),
          "last_accessed": memory.last_accessed.isoformat(),
          "total_memory_items": len(memory.short_term) + len(memory.long_term),
          "memory_limits": self.memory_limits
      }

    except Exception as e:
      logger.error(f"Error getting memory stats: {str(e)}")
      return {"error": str(e)}
