"""
Base task class for background task processing.
"""
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class BaseTask(ABC):
  """
  Base class for all background tasks.
  Provides common task functionality and interface.
  """

  def __init__(
      self,
      task_id: Optional[str] = None,
      task_type: str = "base_task",
      priority: int = 5,
      metadata: Optional[Dict[str, Any]] = None
  ):
    """
    Initialize the base task.

    Args:
        task_id: Unique identifier for the task
        task_type: Type of task for categorization
        priority: Task priority (1=highest, 10=lowest)
        metadata: Additional task metadata
    """
    self.task_id = task_id or str(uuid.uuid4())
    self.task_type = task_type
    self.priority = priority
    self.metadata = metadata or {}
    self.created_at = datetime.now(timezone.utc)
    self.started_at: Optional[datetime] = None
    self.completed_at: Optional[datetime] = None
    self.status = "pending"

  @abstractmethod
  async def execute(self) -> Dict[str, Any]:
    """
    Execute the task.

    Returns:
        Task execution result
    """
    pass

  async def cancel(self) -> None:
    """Cancel the task (default implementation)."""
    self.status = "cancelled"

  def get_status(self) -> Dict[str, Any]:
    """
    Get the current status of the task.

    Returns:
        Status dictionary
    """
    return {
        "task_id": self.task_id,
        "task_type": self.task_type,
        "priority": self.priority,
        "status": self.status,
        "created_at": self.created_at.isoformat(),
        "started_at": self.started_at.isoformat() if self.started_at else None,
        "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        "metadata": self.metadata
    }

  def __str__(self) -> str:
    """String representation of the task."""
    return f"{self.task_type}({self.task_id})"
