"""
Delete call session state from Redis.
"""
from ...connection import get_redis_client
from ....core.logging import get_logger

logger = get_logger(__name__)


async def delete_call_session(call_id: str) -> bool:
    """
    Delete call session data from Redis.
    
    Args:
        call_id: Call identifier
        
    Returns:
        True if successful
    """
    try:
        redis_client = await get_redis_client()
        key = f"call_session:{call_id}"
        
        result = await redis_client.delete(key)
        
        if result:
            logger.debug(f"Deleted session data for call {call_id}")
            return True
        else:
            logger.warning(f"No session data found for call {call_id}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to delete session for call {call_id}: {e}")
        return False


async def clear_expired_sessions() -> int:
    """
    Clear expired call sessions (manual cleanup).
    
    Returns:
        Number of sessions cleared
    """
    try:
        redis_client = await get_redis_client()
        pattern = "call_session:*"
        
        # Find all session keys
        keys = await redis_client.keys(pattern)
        
        # Check each key and delete if expired
        cleared = 0
        for key in keys:
            ttl = await redis_client.ttl(key)
            if ttl == -1:  # No expiration set
                # Set default expiration of 1 hour
                await redis_client.expire(key, 3600)
            elif ttl == -2:  # Key doesn't exist (shouldn't happen here)
                cleared += 1
                
        logger.info(f"Processed {len(keys)} session keys, {cleared} were expired")
        return cleared
        
    except Exception as e:
        logger.error(f"Failed to clear expired sessions: {e}")
        return 0
