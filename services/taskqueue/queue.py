"""Task queue implementation using Redis."""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union

from pydantic import BaseModel
import redis.asyncio as aioredis

from core.config.providers.redis import RedisConfig
from core.logging.setup import get_logger


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


class TaskQueue:
  """Redis-based task queue implementation."""

  def __init__(self, redis_config: RedisConfig, queue_name: str = "default"):
    self.logger = get_logger(__name__)
    self.redis_config = redis_config
    self.queue_name = queue_name
    self._redis_client: Optional[aioredis.Redis] = None

    # Queue keys
    self.pending_key = f"queue:{queue_name}:pending"
    self.processing_key = f"queue:{queue_name}:processing"
    self.completed_key = f"queue:{queue_name}:completed"
    self.failed_key = f"queue:{queue_name}:failed"
    self.task_key_prefix = f"task:{queue_name}"

  @property
  def redis_client(self) -> aioredis.Redis:
    """Get Redis client, ensuring it's connected."""
    if self._redis_client is None:
      raise RuntimeError("Redis client not connected. Call connect() first.")
    return self._redis_client

  async def connect(self) -> None:
    """Connect to Redis."""

    if self._redis_client is None:
      self._redis_client = aioredis.from_url(
          f"redis://{self.redis_config.host}:{self.redis_config.port}",
          password=self.redis_config.password,
          db=self.redis_config.db,
          decode_responses=True
      )

      self.logger.info(f"Connected to Redis for queue: {self.queue_name}")

  async def disconnect(self) -> None:
    """Disconnect from Redis."""

    if self._redis_client:
      await self._redis_client.close()
      self._redis_client = None
      self.logger.info(f"Disconnected from Redis for queue: {self.queue_name}")

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

    if not self._redis_client:
      await self.connect()

    task_id = str(uuid.uuid4())

    task = Task(
        id=task_id,
        name=name,
        data=data,
        priority=priority,
        created_at=datetime.utcnow(),
        scheduled_at=scheduled_at,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds
    )

    # Store task data
    task_key = f"{self.task_key_prefix}:{task_id}"
    # 24 hours TTL
    await self.redis_client.set(task_key, task.json(), ex=86400)

    # Add to appropriate queue
    if scheduled_at and scheduled_at > datetime.utcnow():
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

    if not self._redis_client:
      await self.connect()

    task_key = f"{self.task_key_prefix}:{task_id}"
    task_data = await self.redis_client.get(task_key)

    if not task_data:
      return None

    return Task.parse_raw(task_data)

  async def get_queue_stats(self) -> Dict[str, int]:
    """Get queue statistics."""

    if not self._redis_client:
      await self.connect()

    stats = {
        "pending": await self.redis_client.zcard(self.pending_key),
        "scheduled": await self.redis_client.zcard(f"{self.pending_key}:scheduled"),
        "processing": await self.redis_client.zcard(self.processing_key),
        "completed": await self.redis_client.zcard(self.completed_key),
        "failed": await self.redis_client.zcard(self.failed_key)
    }

    return stats

  async def dequeue(self, timeout: int = 10) -> Optional[Task]:
    """Dequeue a task for processing."""

    if not self._redis_client:
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
    task.started_at = datetime.utcnow()

    await self.redis_client.set(task_key, task.json(), ex=86400)
    await self.redis_client.zadd(self.processing_key, {task_id: datetime.utcnow().timestamp()})

    self.logger.info(f"Dequeued task {task_id}: {task.name}")

    return task

  async def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> None:
    """Mark task as completed."""

    if not self._redis_client:
      await self.connect()

    task_key = f"{self.task_key_prefix}:{task_id}"
    task_data = await self.redis_client.get(task_key)

    if not task_data:
      return

    task = Task.parse_raw(task_data)
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    task.result = result

    # Update task data
    await self.redis_client.set(task_key, task.json(), ex=86400)

    # Move from processing to completed
    await self.redis_client.zrem(self.processing_key, task_id)
    await self.redis_client.zadd(self.completed_key, {task_id: datetime.utcnow().timestamp()})

    self.logger.info(f"Completed task {task_id}")

  async def fail_task(self, task_id: str, error_message: str) -> bool:
    """Mark task as failed, return True if should retry."""

    if not self._redis_client:
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
      await self.redis_client.zadd(self.failed_key, {task_id: datetime.utcnow().timestamp()})

      self.logger.error(
          f"Failed task {task_id} after {task.retry_count} attempts")
      return False

  async def _process_scheduled_tasks(self) -> None:
    """Move ready scheduled tasks to pending queue."""

    current_time = datetime.utcnow().timestamp()
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
        task = await self.get_task(task_id)
        if task:
          score = self._get_priority_score(task.priority)
          await self.redis_client.zadd(self.pending_key, {task_id: score})

  async def cleanup_old_tasks(self, days: int = 7) -> int:
    """Clean up old completed and failed tasks."""

    if not self._redis_client:
      await self.connect()

    cutoff_time = (datetime.utcnow() - timedelta(days=days)).timestamp()

    # Clean completed tasks
    completed_cleaned = await self.redis_client.zremrangebyscore(
        self.completed_key, 0, cutoff_time
    )

    # Clean failed tasks
    failed_cleaned = await self.redis_client.zremrangebyscore(
        self.failed_key, 0, cutoff_time
    )

    total_cleaned = completed_cleaned + failed_cleaned

    if total_cleaned > 0:
      self.logger.info(f"Cleaned up {total_cleaned} old tasks")

    return total_cleaned
