"""Task cleanup and maintenance operations."""

from datetime import datetime, timezone, timedelta

from core.logging.setup import get_logger
from ..connection import RedisConnectionManager


class MaintenanceOperations:
  """Manages task cleanup and maintenance operations."""

  def __init__(self, queue_name: str):
    """Initialize maintenance operations."""
    self.logger = get_logger(__name__)
    self.queue_name = queue_name
    self.connection_manager = RedisConnectionManager(queue_name)

    # Queue keys
    self.completed_key = f"queue:{queue_name}:completed"
    self.failed_key = f"queue:{queue_name}:failed"

  @property
  def redis_client(self):
    """Get Redis client."""
    return self.connection_manager.redis_client

  async def connect(self) -> None:
    """Connect to Redis."""
    await self.connection_manager.connect()

  async def cleanup_old_tasks(self, days: int = 7) -> int:
    """Clean up old completed and failed tasks."""
    if not self.connection_manager.is_connected:
      await self.connect()

    cutoff_time = (datetime.now(timezone.utc) -
                   timedelta(days=days)).timestamp()

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
