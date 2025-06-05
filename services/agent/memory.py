"""
Memory management for agent conversations and context.

This module provides a unified interface to the modularized memory components.
All classes are now organized in their own files within the memory/ subdirectory.
"""

# Import all memory components from the modularized structure
from .memory.models.item import MemoryItem, ConversationMemory
from .memory.manager import MemoryManager
from .memory.conversation.manager import ConversationMemoryManager
from .memory.storage.persistent import MemoryStorage
from .memory.operations.search import MemorySearchManager
from .memory.operations.consolidation import MemoryConsolidationManager
from .memory.operations.cleanup import MemoryCleanupManager

# Maintain backward compatibility
__all__ = [
    "MemoryItem", 
    "ConversationMemory", 
    "MemoryManager",
    "ConversationMemoryManager",
    "MemoryStorage",
    "MemorySearchManager",
    "MemoryConsolidationManager",
    "MemoryCleanupManager"
]
