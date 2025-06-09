"""
Redis connection setup and client management.
"""
import redis.asyncio as redis
from typing import Optional
from core.config.registry import config_registry
from core.logging.setup import get_logger

logger = get_logger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
  """
  Get or create Redis client instance.

  Returns:
      Redis client instance
  """
  global _redis_client

  if _redis_client is None:
    await connect_redis()

  if _redis_client is None:
    raise RuntimeError("Failed to establish Redis connection")

  return _redis_client


async def connect_redis() -> None:
  """Initialize Redis connection."""
  global _redis_client

  try:
    config = config_registry.redis

    # Create async Redis connection for Docker container
    _redis_client = redis.Redis(
        host=config.host,
        port=config.port,
        password=config.password if config.password else None,
        db=config.db,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        retry_on_timeout=True
    )

    # Test connection
    await _redis_client.ping()
    logger.info(f"Redis connection established to {config.host}:{config.port}")

  except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    _redis_client = None
    raise


async def close_redis() -> None:
  """Close Redis connection."""
  global _redis_client

  if _redis_client:
    await _redis_client.aclose()  # Use aclose() for async Redis client
    _redis_client = None
    logger.info("Redis connection closed")
