"""Task processing operations."""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from ..models import Task, TaskStatus
from ..connection import RedisConnectionManager


class ProcessingOperations:
  """Manages task processing operations."""

  def __init__(self, queue_name: str):
    """Initialize processing operations."""
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

  def _get_priority_score(self, priority) -> int:
    """Get numeric score for priority."""
    from ..models import TaskPriority
    priority_scores = {
        TaskPriority.LOW: 1,
        TaskPriority.NORMAL: 2,
        TaskPriority.HIGH: 3,
        TaskPriority.CRITICAL: 4
    }
    return priority_scores.get(priority, 2)

  async def dequeue(self, timeout: int = 10) -> Optional[Task]:
    """Dequeue a task for processing."""
    if not self.connection_manager.is_connected:
      await self.connect()

    # Check for scheduled tasks that are ready
    await self._process_scheduled_tasks()

    # Get highest priority task
    result = await self.redis_client.bzpopmax(self.pending_key, timeout=timeout)

    if not result:
      return None

    _, task_id, _ = result

    # Get task data
    task_key = f"{self.task_key_prefix}:{task_id}"
    task_data = await self.redis_client.get(task_key)

    if not task_data:
      self.logger.warning(f"Task data not found for {task_id}")
      return None

    task = Task.parse_raw(task_data)

    # Move to processing
    task.status = TaskStatus.PROCESSING
    task.started_at = datetime.now(timezone.utc)

    await self.redis_client.set(task_key, task.json(), ex=86400)
    await self.redis_client.zadd(self.processing_key, {task_id: datetime.now(timezone.utc).timestamp()})

    self.logger.info(f"Dequeued task {task_id}: {task.name}")
    return task

  async def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> None:
    """Mark task as completed."""
    if not self.connection_manager.is_connected:
      await self.connect()

    task_key = f"{self.task_key_prefix}:{task_id}"
    task_data = await self.redis_client.get(task_key)

    if not task_data:
      return

    task = Task.parse_raw(task_data)
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.now(timezone.utc)
    task.result = result

    # Update task data
    await self.redis_client.set(task_key, task.json(), ex=86400)

    # Move from processing to completed
    await self.redis_client.zrem(self.processing_key, task_id)
    await self.redis_client.zadd(self.completed_key, {task_id: datetime.now(timezone.utc).timestamp()})

    self.logger.info(f"Completed task {task_id}")

  async def fail_task(self, task_id: str, error_message: str) -> bool:
    """Mark task as failed, return True if should retry."""
    if not self.connection_manager.is_connected:
      await self.connect()

    task_key = f"{self.task_key_prefix}:{task_id}"
    task_data = await self.redis_client.get(task_key)

    if not task_data:
      return False

    task = Task.parse_raw(task_data)
    task.retry_count += 1
    task.error_message = error_message

    # Remove from processing
    await self.redis_client.zrem(self.processing_key, task_id)

    if task.retry_count < task.max_retries:
      # Retry task
      task.status = TaskStatus.RETRYING
      await self.redis_client.set(task_key, task.json(), ex=86400)

      # Re-queue with same priority
      score = self._get_priority_score(task.priority)
      await self.redis_client.zadd(self.pending_key, {task_id: score})

      self.logger.warning(
          f"Retrying task {task_id} (attempt {task.retry_count})")
      return True
    else:
      # Mark as failed
      task.status = TaskStatus.FAILED
      await self.redis_client.set(task_key, task.json(), ex=86400)
      await self.redis_client.zadd(self.failed_key, {task_id: datetime.now(timezone.utc).timestamp()})

      self.logger.error(
          f"Failed task {task_id} after {task.retry_count} attempts")
      return False

  async def _process_scheduled_tasks(self) -> None:
    """Move ready scheduled tasks to pending queue."""
    current_time = datetime.now(timezone.utc).timestamp()
    scheduled_key = f"{self.pending_key}:scheduled"

    # Get tasks ready to run
    ready_tasks = await self.redis_client.zrangebyscore(
        scheduled_key, 0, current_time, withscores=True
    )

    if ready_tasks:
      # Move to pending queue
      for task_id, _ in ready_tasks:
        # Remove from scheduled
        await self.redis_client.zrem(scheduled_key, task_id)

        # Get task to determine priority
        task_key = f"{self.task_key_prefix}:{task_id}"
        task_data = await self.redis_client.get(task_key)
        if task_data:
          task = Task.parse_raw(task_data)
          score = self._get_priority_score(task.priority)
          await self.redis_client.zadd(self.pending_key, {task_id: score})
