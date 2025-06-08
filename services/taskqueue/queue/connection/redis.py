"""Redis connection manager for task queue."""

from typing import Optional

import redis.asyncio as aioredis

from core.config.registry import config_registry
from core.logging.setup import get_logger


class RedisConnectionManager:
  """Manages Redis connections for task queue."""

  def __init__(self, queue_name: str):
    """Initialize connection manager."""
    self.logger = get_logger(__name__)
    self.redis_config = config_registry.redis
    self.queue_name = queue_name
    self._redis_client: Optional[aioredis.Redis] = None

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

  @property
  def is_connected(self) -> bool:
    """Check if Redis client is connected."""
    return self._redis_client is not None
