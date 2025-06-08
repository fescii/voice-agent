"""Task queue operations manager."""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from ..models import Task, TaskStatus, TaskPriority
from ..connection import RedisConnectionManager


class QueueOperations:
  """Manages basic queue operations."""

  def __init__(self, queue_name: str):
    """Initialize queue operations."""
    self.logger = get_logger(__name__)
    self.queue_name = queue_name
    self.connection_manager = RedisConnectionManager(queue_name)

    # Queue keys
    self.pending_key = f"queue:{queue_name}:pending"
    self.processing_key = f"queue:{queue_name}:processing"
    self.completed_key = f"queue:{queue_name}:completed"
    self.failed_key = f"queue:{queue_name}:failed"
    self.task_key_prefix = f"task:{queue_name}"

  @property
  def redis_client(self):
    """Get Redis client."""
    return self.connection_manager.redis_client

  async def connect(self) -> None:
    """Connect to Redis."""
    await self.connection_manager.connect()

  async def disconnect(self) -> None:
    """Disconnect from Redis."""
    await self.connection_manager.disconnect()

  def _get_priority_score(self, priority: TaskPriority) -> int:
    """Get numeric score for priority."""
    priority_scores = {
        TaskPriority.LOW: 1,
        TaskPriority.NORMAL: 2,
        TaskPriority.HIGH: 3,
        TaskPriority.CRITICAL: 4
    }
    return priority_scores.get(priority, 2)

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
    if not self.connection_manager.is_connected:
      await self.connect()

    task_id = str(uuid.uuid4())

    task = Task(
        id=task_id,
        name=name,
        data=data,
        priority=priority,
        created_at=datetime.now(timezone.utc),
        scheduled_at=scheduled_at,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds
    )

    # Store task data
    task_key = f"{self.task_key_prefix}:{task_id}"
    # 24 hours TTL
    await self.redis_client.set(task_key, task.json(), ex=86400)

    # Add to appropriate queue
    if scheduled_at and scheduled_at > datetime.now(timezone.utc):
      # Scheduled task
      score = scheduled_at.timestamp()
      await self.redis_client.zadd(f"{self.pending_key}:scheduled", {task_id: score})
    else:
      # Immediate task
      score = self._get_priority_score(priority)
      await self.redis_client.zadd(self.pending_key, {task_id: score})

    self.logger.info(f"Enqueued task {task_id}: {name}")
    return task_id

  async def get_task(self, task_id: str) -> Optional[Task]:
    """Get task by ID."""
    if not self.connection_manager.is_connected:
      await self.connect()

    task_key = f"{self.task_key_prefix}:{task_id}"
    task_data = await self.redis_client.get(task_key)

    if not task_data:
      return None

    return Task.parse_raw(task_data)

  async def get_queue_stats(self) -> Dict[str, int]:
    """Get queue statistics."""
    if not self.connection_manager.is_connected:
      await self.connect()

    stats = {
        "pending": await self.redis_client.zcard(self.pending_key),
        "scheduled": await self.redis_client.zcard(f"{self.pending_key}:scheduled"),
        "processing": await self.redis_client.zcard(self.processing_key),
        "completed": await self.redis_client.zcard(self.completed_key),
        "failed": await self.redis_client.zcard(self.failed_key)
    }

    return stats
