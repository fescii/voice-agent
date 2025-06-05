"""
Redis connection setup and client management.
"""
import redis.asyncio as redis
from typing import Optional
from ..core.config.providers.redis import RedisConfig
from ..core.logging import get_logger

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
    
    return _redis_client


async def connect_redis() -> None:
    """Initialize Redis connection."""
    global _redis_client
    
    try:
        config = RedisConfig()
        
        _redis_client = redis.Redis(
            host=config.host,
            port=config.port,
            password=config.password,
            db=config.database,
            decode_responses=True,
            health_check_interval=30,
            socket_keepalive=True,
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 5,  # TCP_KEEPCNT
            }
        )
        
        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established")
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")
