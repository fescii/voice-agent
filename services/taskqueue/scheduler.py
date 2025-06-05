"""Task scheduler for managing scheduled and recurring tasks."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Callable, Any
from enum import Enum

from pydantic import BaseModel

from core.logging.setup import get_logger
from .queue import TaskQueue, TaskPriority


class ScheduleType(str, Enum):
  """Schedule type enumeration."""

  ONCE = "once"
  RECURRING = "recurring"
  CRON = "cron"


class ScheduledTask(BaseModel):
  """Scheduled task model."""

  id: str
  name: str
  data: Dict[str, Any]
  schedule_type: ScheduleType
  next_run: datetime
  interval_seconds: Optional[int] = None
  cron_expression: Optional[str] = None
  priority: TaskPriority = TaskPriority.NORMAL
  max_retries: int = 3
  timeout_seconds: int = 300
  is_active: bool = True
  created_at: datetime
  last_run: Optional[datetime] = None
  run_count: int = 0


class TaskScheduler:
  """Scheduler for managing scheduled and recurring tasks."""

  def __init__(self, task_queue: TaskQueue):
    self.logger = get_logger(__name__)
    self.task_queue = task_queue
    self.scheduled_tasks: Dict[str, ScheduledTask] = {}
    self.is_running = False
    self._scheduler_task: Optional[asyncio.Task] = None

  async def start(self) -> None:
    """Start the task scheduler."""

    if self.is_running:
      return

    self.logger.info("Starting task scheduler")
    self.is_running = True

    # Start scheduler loop
    self._scheduler_task = asyncio.create_task(self._scheduler_loop())

  async def stop(self) -> None:
    """Stop the task scheduler."""

    if not self.is_running:
      return

    self.logger.info("Stopping task scheduler")
    self.is_running = False

    if self._scheduler_task and not self._scheduler_task.done():
      self._scheduler_task.cancel()
      try:
        await self._scheduler_task
      except asyncio.CancelledError:
        pass

    self.logger.info("Task scheduler stopped")

  async def schedule_once(
      self,
      task_id: str,
      name: str,
      data: Dict[str, Any],
      run_at: datetime,
      priority: TaskPriority = TaskPriority.NORMAL,
      max_retries: int = 3,
      timeout_seconds: int = 300
  ) -> None:
    """Schedule a task to run once at a specific time."""

    scheduled_task = ScheduledTask(
        id=task_id,
        name=name,
        data=data,
        schedule_type=ScheduleType.ONCE,
        next_run=run_at,
        priority=priority,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        created_at=datetime.utcnow()
    )

    self.scheduled_tasks[task_id] = scheduled_task

    self.logger.info(f"Scheduled one-time task {task_id} for {run_at}")

  async def schedule_recurring(
      self,
      task_id: str,
      name: str,
      data: Dict[str, Any],
      interval_seconds: int,
      start_at: Optional[datetime] = None,
      priority: TaskPriority = TaskPriority.NORMAL,
      max_retries: int = 3,
      timeout_seconds: int = 300
  ) -> None:
    """Schedule a recurring task."""

    if start_at is None:
      start_at = datetime.utcnow() + timedelta(seconds=interval_seconds)

    scheduled_task = ScheduledTask(
        id=task_id,
        name=name,
        data=data,
        schedule_type=ScheduleType.RECURRING,
        next_run=start_at,
        interval_seconds=interval_seconds,
        priority=priority,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        created_at=datetime.utcnow()
    )

    self.scheduled_tasks[task_id] = scheduled_task

    self.logger.info(
        f"Scheduled recurring task {task_id} every {interval_seconds}s starting {start_at}"
    )

  async def schedule_cron(
      self,
      task_id: str,
      name: str,
      data: Dict[str, Any],
      cron_expression: str,
      priority: TaskPriority = TaskPriority.NORMAL,
      max_retries: int = 3,
      timeout_seconds: int = 300
  ) -> None:
    """Schedule a task using cron expression."""

    # Calculate next run time from cron expression
    next_run = self._calculate_next_cron_run(cron_expression)

    scheduled_task = ScheduledTask(
        id=task_id,
        name=name,
        data=data,
        schedule_type=ScheduleType.CRON,
        next_run=next_run,
        cron_expression=cron_expression,
        priority=priority,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        created_at=datetime.utcnow()
    )

    self.scheduled_tasks[task_id] = scheduled_task

    self.logger.info(
        f"Scheduled cron task {task_id} with expression '{cron_expression}'")

  async def unschedule_task(self, task_id: str) -> bool:
    """Unschedule a task."""

    if task_id in self.scheduled_tasks:
      del self.scheduled_tasks[task_id]
      self.logger.info(f"Unscheduled task {task_id}")
      return True

    return False

  async def pause_task(self, task_id: str) -> bool:
    """Pause a scheduled task."""

    if task_id in self.scheduled_tasks:
      self.scheduled_tasks[task_id].is_active = False
      self.logger.info(f"Paused task {task_id}")
      return True

    return False

  async def resume_task(self, task_id: str) -> bool:
    """Resume a paused task."""

    if task_id in self.scheduled_tasks:
      self.scheduled_tasks[task_id].is_active = True
      self.logger.info(f"Resumed task {task_id}")
      return True

    return False

  async def get_scheduled_tasks(self) -> List[ScheduledTask]:
    """Get all scheduled tasks."""
    return list(self.scheduled_tasks.values())

  async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
    """Get a specific scheduled task."""
    return self.scheduled_tasks.get(task_id)

  async def _scheduler_loop(self) -> None:
    """Main scheduler loop."""

    while self.is_running:
      try:
        current_time = datetime.utcnow()

        # Check for tasks that need to run
        for task_id, scheduled_task in self.scheduled_tasks.copy().items():
          if not scheduled_task.is_active:
            continue

          if scheduled_task.next_run <= current_time:
            await self._execute_scheduled_task(scheduled_task)

        # Sleep for a short interval
        await asyncio.sleep(1)

      except Exception as e:
        self.logger.error(f"Error in scheduler loop: {e}")
        await asyncio.sleep(5)

  async def _execute_scheduled_task(self, scheduled_task: ScheduledTask) -> None:
    """Execute a scheduled task."""

    try:
      # Enqueue the task
      await self.task_queue.enqueue(
          name=scheduled_task.name,
          data=scheduled_task.data,
          priority=scheduled_task.priority,
          max_retries=scheduled_task.max_retries,
          timeout_seconds=scheduled_task.timeout_seconds
      )

      # Update task statistics
      scheduled_task.last_run = datetime.utcnow()
      scheduled_task.run_count += 1

      self.logger.info(f"Executed scheduled task {scheduled_task.id}")

      # Calculate next run time
      await self._calculate_next_run(scheduled_task)

    except Exception as e:
      self.logger.error(
          f"Failed to execute scheduled task {scheduled_task.id}: {e}")

  async def _calculate_next_run(self, scheduled_task: ScheduledTask) -> None:
    """Calculate the next run time for a task."""

    if scheduled_task.schedule_type == ScheduleType.ONCE:
      # One-time task, remove it
      self.scheduled_tasks.pop(scheduled_task.id, None)
      self.logger.info(f"Removed one-time task {scheduled_task.id}")

    elif scheduled_task.schedule_type == ScheduleType.RECURRING:
      # Recurring task, calculate next run
      if scheduled_task.interval_seconds:
        scheduled_task.next_run = datetime.utcnow() + timedelta(
            seconds=scheduled_task.interval_seconds
        )

    elif scheduled_task.schedule_type == ScheduleType.CRON:
      # Cron task, calculate next run from expression
      if scheduled_task.cron_expression:
        scheduled_task.next_run = self._calculate_next_cron_run(
            scheduled_task.cron_expression
        )

  def _calculate_next_cron_run(self, cron_expression: str) -> datetime:
    """Calculate next run time from cron expression."""

    # Simplified cron parser - in production, use a proper cron library
    # This is a basic implementation for common patterns

    parts = cron_expression.split()
    if len(parts) != 5:
      raise ValueError("Invalid cron expression format")

    # For now, just add 1 hour as a placeholder
    # In production, implement proper cron parsing
    return datetime.utcnow() + timedelta(hours=1)

  async def get_scheduler_stats(self) -> Dict[str, Any]:
    """Get scheduler statistics."""

    active_tasks = sum(
        1 for task in self.scheduled_tasks.values() if task.is_active)

    stats = {
        "is_running": self.is_running,
        "total_tasks": len(self.scheduled_tasks),
        "active_tasks": active_tasks,
        "paused_tasks": len(self.scheduled_tasks) - active_tasks,
        "schedule_types": {
            schedule_type.value: sum(
                1 for task in self.scheduled_tasks.values()
                if task.schedule_type == schedule_type
            )
            for schedule_type in ScheduleType
        }
    }

    return stats
