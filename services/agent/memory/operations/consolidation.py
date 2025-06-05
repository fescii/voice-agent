"""
Memory consolidation operations.
"""
from typing import Dict, List, Tuple, Any
from datetime import datetime
from core.logging.setup import get_logger
from ..models.item import ConversationMemory, MemoryItem

logger = get_logger(__name__)


class MemoryConsolidationManager:
  """Handles memory consolidation and optimization."""

  async def promote_to_long_term(
      self,
      memory: ConversationMemory,
      key: str,
      importance_threshold: float = 0.7
  ):
    """
    Promote short-term memory to long-term based on importance.

    Args:
        memory: Conversation memory
        key: Memory key
        importance_threshold: Minimum importance for promotion
    """
    try:
      if key in memory.short_term:
        memory_item = memory.short_term[key]

        # Check importance and access count
        if (memory_item.importance >= importance_threshold or
                memory_item.access_count >= 3):

          # Move to long-term memory
          memory.long_term[key] = memory_item
          del memory.short_term[key]

          logger.info(f"Promoted memory to long-term: {key}")

    except Exception as e:
      logger.error(f"Error promoting memory: {str(e)}")

  async def consolidate_memories(self, memory: ConversationMemory):
    """
    Consolidate and optimize memory for a conversation.

    Args:
        memory: Conversation memory to consolidate
    """
    try:
      # Promote frequently accessed items
      for key, memory_item in list(memory.short_term.items()):
        if memory_item.access_count >= 3 or memory_item.importance >= 0.8:
          await self.promote_to_long_term(memory, key)

      # Remove low-importance, unused items
      await self._cleanup_unused_memories(memory)

      # Merge similar memories
      await self._merge_similar_memories(memory)

      logger.info(
          f"Consolidated memory for conversation: {memory.conversation_id}")

    except Exception as e:
      logger.error(f"Error consolidating memories: {str(e)}")

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

  async def enforce_memory_limits(
      self,
      memory_dict: Dict[str, MemoryItem],
      max_items: int
  ):
    """Enforce memory limits by removing least important items."""
    try:
      if len(memory_dict) > max_items:
        # Sort by importance and access patterns
        items = list(memory_dict.items())
        items.sort(key=lambda x: (
            x[1].importance,
            x[1].access_count,
            x[1].timestamp
        ))

        # Remove least important items
        items_to_remove = items[:len(items) - max_items]
        for key, _ in items_to_remove:
          del memory_dict[key]

        logger.debug(f"Removed {len(items_to_remove)} items to enforce limits")

    except Exception as e:
      logger.warning(f"Error enforcing memory limits: {str(e)}")

  async def enforce_working_memory_limits(
      self,
      working_memory: Dict[str, Any],
      max_items: int
  ):
    """Enforce working memory limits."""
    try:
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
