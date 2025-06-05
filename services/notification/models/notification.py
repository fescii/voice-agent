"""
Notification model and related enums.
"""

import time
from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass


class NotificationPriority(Enum):
  """Notification priority levels."""
  LOW = "low"
  NORMAL = "normal"
  HIGH = "high"
  URGENT = "urgent"


class NotificationStatus(Enum):
  """Notification status."""
  PENDING = "pending"
  SENT = "sent"
  FAILED = "failed"
  RETRY = "retry"


@dataclass
class Notification:
  """Notification data structure."""
  id: str
  type: str
  priority: NotificationPriority
  recipient: str
  subject: str
  message: str
  data: Dict[str, Any]
  channel: str
  status: NotificationStatus = NotificationStatus.PENDING
  created_at: Optional[float] = None
  sent_at: Optional[float] = None
  retry_count: int = 0
  max_retries: int = 3

  def __post_init__(self):
    if self.created_at is None:
      self.created_at = time.time()
