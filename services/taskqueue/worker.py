"""Task worker for processing queued tasks."""

import asyncio
import signal
from datetime import datetime
from typing import Dict, Callable, Any, Optional

from core.logging.setup import get_logger
from .queue import TaskQueue, Task, TaskStatus


class TaskWorker:
  """Worker for processing tasks from a queue."""

  def __init__(self, task_queue: TaskQueue, worker_id: str = "default"):
    self.logger = get_logger(__name__)
    self.task_queue = task_queue
    self.worker_id = worker_id
    self.handlers: Dict[str, Callable] = {}
    self.is_running = False
    self.current_task: Optional[Task] = None
    self.stats = {
        "processed": 0,
        "completed": 0,
        "failed": 0,
        "started_at": None
    }

  def register_handler(self, task_name: str, handler: Callable) -> None:
    """Register a handler for a specific task type."""
    self.handlers[task_name] = handler
    self.logger.info(f"Registered handler for task: {task_name}")

  async def start(self) -> None:
    """Start the worker."""

    if self.is_running:
      return

    self.logger.info(f"Starting task worker: {self.worker_id}")

    self.is_running = True
    self.stats["started_at"] = datetime.utcnow()

    # Setup signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    for sig in [signal.SIGTERM, signal.SIGINT]:
      loop.add_signal_handler(sig, self.stop)

    try:
      await self._worker_loop()
    except Exception as e:
      self.logger.error(f"Worker error: {e}")
    finally:
      self.is_running = False
      self.logger.info(f"Task worker stopped: {self.worker_id}")

  def stop(self) -> None:
    """Stop the worker gracefully."""
    self.logger.info(f"Stopping task worker: {self.worker_id}")
    self.is_running = False

  async def _worker_loop(self) -> None:
    """Main worker loop."""

    while self.is_running:
      try:
        # Dequeue task with timeout
        task = await self.task_queue.dequeue(timeout=5)

        if task is None:
          continue

        self.current_task = task
        self.stats["processed"] += 1

        await self._process_task(task)

      except Exception as e:
        self.logger.error(f"Error in worker loop: {e}")
        await asyncio.sleep(1)
      finally:
        self.current_task = None

  async def _process_task(self, task: Task) -> None:
    """Process a single task."""

    start_time = datetime.utcnow()

    try:
      self.logger.info(f"Processing task {task.id}: {task.name}")

      # Get handler for task
      handler = self.handlers.get(task.name)
      if not handler:
        raise ValueError(f"No handler registered for task: {task.name}")

      # Execute task with timeout
      result = await asyncio.wait_for(
          self._execute_handler(handler, task),
          timeout=task.timeout_seconds
      )

      # Mark as completed
      await self.task_queue.complete_task(task.id, result)
      self.stats["completed"] += 1

      duration = (datetime.utcnow() - start_time).total_seconds()
      self.logger.info(
          f"Completed task {task.id} in {duration:.2f}s"
      )

    except asyncio.TimeoutError:
      error_msg = f"Task timed out after {task.timeout_seconds}s"
      await self._handle_task_failure(task, error_msg)

    except Exception as e:
      error_msg = f"Task execution failed: {str(e)}"
      await self._handle_task_failure(task, error_msg)

  async def _execute_handler(self, handler: Callable, task: Task) -> Any:
    """Execute task handler."""

    if asyncio.iscoroutinefunction(handler):
      return await handler(task.data)
    else:
      # Run sync handler in thread pool
      loop = asyncio.get_event_loop()
      return await loop.run_in_executor(None, handler, task.data)

  async def _handle_task_failure(self, task: Task, error_message: str) -> None:
    """Handle task failure."""

    self.logger.error(f"Task {task.id} failed: {error_message}")

    # Attempt to retry or mark as failed
    should_retry = await self.task_queue.fail_task(task.id, error_message)

    if should_retry:
      self.logger.info(f"Task {task.id} queued for retry")
    else:
      self.logger.error(f"Task {task.id} permanently failed")
      self.stats["failed"] += 1

  def get_stats(self) -> Dict[str, Any]:
    """Get worker statistics."""

    stats = self.stats.copy()
    stats["worker_id"] = self.worker_id
    stats["is_running"] = self.is_running
    stats["current_task"] = self.current_task.dict(
    ) if self.current_task else None
    stats["registered_handlers"] = list(self.handlers.keys())

    if stats["started_at"]:
      uptime = (datetime.utcnow() - stats["started_at"]).total_seconds()
      stats["uptime_seconds"] = uptime

    return stats

  async def health_check(self) -> Dict[str, Any]:
    """Perform health check."""

    health = {
        "worker_id": self.worker_id,
        "is_running": self.is_running,
        "handlers_count": len(self.handlers),
        "current_task_id": self.current_task.id if self.current_task else None,
        "queue_connected": True  # Basic check
    }

    try:
      # Test queue connection
      await self.task_queue.get_queue_stats()
      health["queue_connected"] = True
    except Exception as e:
      health["queue_connected"] = False
      health["queue_error"] = str(e)

    return health
