"""
Modular task queue implementation using Redis.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from .models import Task, TaskStatus, TaskPriority
from .operations import QueueOperations, ProcessingOperations, MaintenanceOperations


class TaskQueue:
  """Redis-based task queue implementation - modular version."""

  def __init__(self, queue_name: str = "default"):
    """Initialize task queue with modular components."""
    self.queue_name = queue_name

    # Initialize modular components
    self.queue_ops = QueueOperations(queue_name)
    self.processing_ops = ProcessingOperations(queue_name)
    self.maintenance_ops = MaintenanceOperations(queue_name)

  async def connect(self) -> None:
    """Connect to Redis."""
    await self.queue_ops.connect()

  async def disconnect(self) -> None:
    """Disconnect from Redis."""
    await self.queue_ops.disconnect()

  async def enqueue(
      self,
      name: str,
      data: Dict[str, Any],
      priority: TaskPriority = TaskPriority.NORMAL,
      scheduled_at: Optional[datetime] = None,
      max_retries: int = 3,
      timeout_seconds: int = 300
  ) -> str:
    """Enqueue a task."""
    return await self.queue_ops.enqueue(
        name, data, priority, scheduled_at, max_retries, timeout_seconds
    )

  async def get_task(self, task_id: str) -> Optional[Task]:
    """Get task by ID."""
    return await self.queue_ops.get_task(task_id)

  async def get_queue_stats(self) -> Dict[str, int]:
    """Get queue statistics."""
    return await self.queue_ops.get_queue_stats()

  async def dequeue(self, timeout: int = 10) -> Optional[Task]:
    """Dequeue a task for processing."""
    return await self.processing_ops.dequeue(timeout)

  async def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> None:
    """Mark task as completed."""
    await self.processing_ops.complete_task(task_id, result)

  async def fail_task(self, task_id: str, error_message: str) -> bool:
    """Mark task as failed, return True if should retry."""
    return await self.processing_ops.fail_task(task_id, error_message)

  async def cleanup_old_tasks(self, days: int = 7) -> int:
    """Clean up old completed and failed tasks."""
    return await self.maintenance_ops.cleanup_old_tasks(days)
