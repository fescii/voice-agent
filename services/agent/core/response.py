"""
Agent response model.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class AgentResponse:
  """Agent response structure."""
  text: str
  audio_data: Optional[bytes] = None
  action: Optional[str] = None
  confidence: float = 1.0
  thinking_time: float = 0.0
  metadata: Optional[Dict[str, Any]] = None
