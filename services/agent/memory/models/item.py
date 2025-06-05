"""
Memory data models and structures.
"""
from typing import Dict, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime


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
