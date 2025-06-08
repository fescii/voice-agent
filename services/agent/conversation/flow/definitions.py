"""
Conversation flow definitions and states.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any
import time


class ConversationFlow(Enum):
  """Conversation flow states."""
  GREETING = "greeting"
  GATHERING_INFO = "gathering_info"
  PROCESSING_REQUEST = "processing_request"
  PROVIDING_SOLUTION = "providing_solution"
  CONFIRMING = "confirming"
  CLOSING = "closing"
  ERROR_HANDLING = "error_handling"


@dataclass
class ConversationTurn:
  """Single conversation turn."""
  user_input: str
  agent_response: str
  timestamp: float
  flow_state: ConversationFlow
  confidence: float
  metadata: Dict[str, Any]
