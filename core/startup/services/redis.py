"""
Redis startup service.
"""
from typing import Dict, Any, TYPE_CHECKING

from .base import BaseStartupService
from data.redis.connection import connect_redis, get_redis_client, close_redis
from core.logging.setup import get_logger

if TYPE_CHECKING:
  from core.startup.manager import StartupContext

logger = get_logger(__name__)


class RedisService(BaseStartupService):
  """Redis initialization service."""

  def __init__(self):
    super().__init__("redis", is_critical=True)

  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """Initialize Redis connection and verify connectivity."""
    try:
      # Initialize Redis connection
      await connect_redis()

      # Test Redis connectivity
      redis_client = await get_redis_client()
      info = await redis_client.info()

      logger.info("Redis connection verified")

      return {
          "redis_version": info.get("redis_version", "unknown"),
          "used_memory": info.get("used_memory_human", "unknown"),
          "connected_clients": info.get("connected_clients", 0),
          "uptime_seconds": info.get("uptime_in_seconds", 0),
          "keyspace": {k: v for k, v in info.items() if k.startswith("db")}
      }

    except Exception as e:
      logger.error(f"Redis connection failed: {e}")
      raise

  async def cleanup(self, context: "StartupContext") -> None:
    """Close Redis connections."""
    try:
      await close_redis()
      logger.info("Redis connections closed")
    except Exception as e:
      logger.error(f"Error closing Redis connections: {e}")

  def get_health_check(self) -> Dict[str, Any]:
    """Get Redis health information."""
    try:
      # This would need to be async in a real health check
      return {
          "service": self.name,
          "status": "healthy",
          "critical": self.is_critical
      }
    except Exception as e:
      return {
          "service": self.name,
          "status": "unhealthy",
          "critical": self.is_critical,
          "error": str(e)
      }
