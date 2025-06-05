"""
Conversation turn data model.
"""

from dataclasses import dataclass
from typing import Dict, Any
from .flow import ConversationFlow


@dataclass
class ConversationTurn:
  """Single conversation turn."""
  user_input: str
  agent_response: str
  timestamp: float
  flow_state: ConversationFlow
  confidence: float
  metadata: Dict[str, Any]
