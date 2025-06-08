"""Task queue models and enums."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class TaskStatus(str, Enum):
  """Task status enumeration."""

  PENDING = "pending"
  PROCESSING = "processing"
  COMPLETED = "completed"
  FAILED = "failed"
  RETRYING = "retrying"


class TaskPriority(str, Enum):
  """Task priority enumeration."""

  LOW = "low"
  NORMAL = "normal"
  HIGH = "high"
  CRITICAL = "critical"


class Task(BaseModel):
  """Task model."""

  id: str
  name: str
  data: Dict[str, Any]
  status: TaskStatus = TaskStatus.PENDING
  priority: TaskPriority = TaskPriority.NORMAL
  created_at: datetime
  scheduled_at: Optional[datetime] = None
  started_at: Optional[datetime] = None
  completed_at: Optional[datetime] = None
  retry_count: int = 0
  max_retries: int = 3
  timeout_seconds: int = 300
  error_message: Optional[str] = None
  result: Optional[Dict[str, Any]] = None
