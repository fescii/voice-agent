"""
Agent state enumeration.
"""
from enum import Enum


class AgentState(Enum):
  """Agent states during conversation."""
  IDLE = "idle"
  LISTENING = "listening"
  THINKING = "thinking"
  SPEAKING = "speaking"
  WAITING = "waiting"
  ERROR = "error"
