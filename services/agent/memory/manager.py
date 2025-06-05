"""
Main memory manager orchestrating all memory operations.
"""
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from core.logging.setup import get_logger
from .conversation.manager import ConversationMemoryManager
from .models.item import ConversationMemory
from .operations.search import MemorySearchManager
from .operations.consolidation import MemoryConsolidationManager
from .operations.cleanup import MemoryCleanupManager

logger = get_logger(__name__)


class MemoryManager:
  """Main memory manager for agent conversations."""

  def __init__(self, agent_id: str):
    """Initialize memory manager."""
    self.agent_id = agent_id
    self.conversations: Dict[str, ConversationMemory] = {}
    self.global_memory: Dict[str, Any] = {}

    # Initialize sub-managers
    self.conversation_manager = ConversationMemoryManager(agent_id)
    self.search_manager = MemorySearchManager()
    self.consolidation_manager = MemoryConsolidationManager()
    self.cleanup_manager = MemoryCleanupManager(agent_id)

    self.memory_limits = {
        "short_term_max": 100,
        "long_term_max": 1000,
        "working_memory_max": 20,
        "global_memory_max": 5000
    }

  async def initialize_conversation_memory(self, conversation_id: str) -> ConversationMemory:
    """Initialize memory for a new conversation."""
    try:
      memory = await self.conversation_manager.initialize_conversation_memory(conversation_id)
      self.conversations[conversation_id] = memory
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
      importance: float = 1.0,
      ttl: Optional[int] = None,
      tags: Optional[Set[str]] = None
  ):
    """Store information in memory."""
    try:
      if conversation_id not in self.conversations:
        await self.initialize_conversation_memory(conversation_id)

      memory = self.conversations[conversation_id]

      await self.conversation_manager.store_memory(
          conversation_id, key, value, memory_type, importance, ttl, tags
      )

      # Update local reference
      self.conversations[conversation_id] = memory

    except Exception as e:
      logger.error(f"Error storing memory: {str(e)}")
      raise

  async def retrieve_memory(
      self,
      conversation_id: str,
      key: str,
      memory_type: str = "short_term"
  ) -> Optional[Any]:
    """Retrieve information from memory."""
    try:
      if conversation_id not in self.conversations:
        await self.initialize_conversation_memory(conversation_id)

      return await self.conversation_manager.retrieve_memory(
          conversation_id, key, memory_type
      )

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
    """Search memory by query and tags."""
    try:
      if conversation_id not in self.conversations:
        return []

      memory = self.conversations[conversation_id]
      return await self.search_manager.search_memory(
          memory, query, memory_types, tags
      )

    except Exception as e:
      logger.error(f"Error searching memory: {str(e)}")
      return []

  async def delete_memory(
      self,
      conversation_id: str,
      key: str,
      memory_type: str = "short_term"
  ):
    """Delete information from memory."""
    try:
      if conversation_id not in self.conversations:
        return

      await self.conversation_manager.delete_memory(
          conversation_id, key, memory_type
      )

    except Exception as e:
      logger.error(f"Error deleting memory: {str(e)}")

  async def promote_to_long_term(
      self,
      conversation_id: str,
      key: str,
      importance_threshold: float = 0.7
  ):
    """Promote short-term memory to long-term."""
    try:
      if conversation_id not in self.conversations:
        return

      memory = self.conversations[conversation_id]
      await self.consolidation_manager.promote_to_long_term(
          memory, key, importance_threshold
      )

    except Exception as e:
      logger.error(f"Error promoting memory: {str(e)}")

  async def consolidate_memories(self, conversation_id: str):
    """Consolidate and optimize memory for a conversation."""
    try:
      if conversation_id not in self.conversations:
        return

      memory = self.conversations[conversation_id]
      await self.consolidation_manager.consolidate_memories(memory)

    except Exception as e:
      logger.error(f"Error consolidating memories: {str(e)}")

  async def cleanup_old_conversations(self, max_age_hours: int = 24):
    """Clean up old conversation memories."""
    try:
      removed_conversations = await self.cleanup_manager.cleanup_old_conversations(
          self.conversations, max_age_hours
      )

      # Remove from local storage
      for conversation_id in removed_conversations:
        if conversation_id in self.conversations:
          del self.conversations[conversation_id]

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
