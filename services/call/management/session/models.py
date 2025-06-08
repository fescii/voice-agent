"""
Call session definitions and models.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
from models.internal.callcontext import CallContext
from services.ringover import CallInfo


class CallPriority(Enum):
  """Call priority levels."""
  LOW = 1
  NORMAL = 2
  HIGH = 3
  URGENT = 4


@dataclass
class CallSession:
  """Represents an active call session."""
  call_id: str
  agent_id: str
  call_context: CallContext
  call_info: CallInfo
  priority: CallPriority = CallPriority.NORMAL
  created_at: datetime = field(default_factory=datetime.now)
  last_activity: datetime = field(default_factory=datetime.now)
  metadata: Dict[str, Any] = field(default_factory=dict)

  # Session state
  is_active: bool = True
  is_streaming: bool = False
  script_name: Optional[str] = None

  # Performance metrics
  response_times: List[float] = field(default_factory=list)
  error_count: int = 0
  audio_quality_score: Optional[float] = None
