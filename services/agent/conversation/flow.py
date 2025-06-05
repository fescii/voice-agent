"""
Conversation flow states.
"""
from enum import Enum


class ConversationFlow(Enum):
  """Conversation flow states."""
  GREETING = "greeting"
  GATHERING_INFO = "gathering_info"
  PROCESSING_REQUEST = "processing_request"
  PROVIDING_SOLUTION = "providing_solution"
  CONFIRMING = "confirming"
  CLOSING = "closing"
  ERROR_HANDLING = "error_handling"
