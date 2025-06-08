"""
Memory search operations.
"""
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone
from core.logging.setup import get_logger
from ..models.item import ConversationMemory, MemoryItem

logger = get_logger(__name__)


class MemorySearchManager:
  """Handles memory search operations."""

  async def search_memory(
      self,
      memory: ConversationMemory,
      query: str,
      memory_types: Optional[List[str]] = None,
      tags: Optional[Set[str]] = None
  ) -> List[Dict[str, Any]]:
    """
    Search memory by query and tags.

    Args:
        memory: Conversation memory to search
        query: Search query
        memory_types: Types of memory to search
        tags: Tags to filter by

    Returns:
        List of matching memory items
    """
    try:
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

  async def find_similar_memories(
      self,
      memory: ConversationMemory,
      target_key: str,
      similarity_threshold: float = 0.8
  ) -> List[str]:
    """Find memories similar to the target key."""
    try:
      similar_keys = []

      # Simple similarity based on key prefix/structure
      base_target = target_key.split("_")[0]

      for memory_type in ["short_term", "long_term"]:
        items = memory.short_term if memory_type == "short_term" else memory.long_term

        for key in items.keys():
          if key != target_key:
            base_key = key.split("_")[0]
            if base_key == base_target:
              similar_keys.append(key)

      return similar_keys

    except Exception as e:
      logger.error(f"Error finding similar memories: {str(e)}")
      return []
