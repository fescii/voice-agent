"""
Store call session state in Redis.
"""
import json
from typing import Dict, Any, Optional
from ...connection import get_redis_client
from ....core.logging import get_logger

logger = get_logger(__name__)


async def store_call_session(
    call_id: str,
    session_data: Dict[str, Any],
    ttl: int = 3600
) -> bool:
  """
  Store call session data in Redis.

  Args:
      call_id: Call identifier
      session_data: Session data to store
      ttl: Time to live in seconds (default 1 hour)

  Returns:
      True if successful
  """
  try:
    redis_client = await get_redis_client()
    key = f"call_session:{call_id}"

    # Serialize data to JSON
    serialized_data = json.dumps(session_data, default=str)

    # Store with TTL
    await redis_client.setex(key, ttl, serialized_data)

    logger.debug(f"Stored session data for call {call_id}")
    return True

  except Exception as e:
    logger.error(f"Failed to store session for call {call_id}: {e}")
    return False


async def update_call_session(
    call_id: str,
    updates: Dict[str, Any],
    ttl: Optional[int] = None
) -> bool:
  """
  Update existing call session data.

  Args:
      call_id: Call identifier
      updates: Data to update
      ttl: Optional new TTL

  Returns:
      True if successful
  """
  try:
    redis_client = await get_redis_client()
    key = f"call_session:{call_id}"

    # Get existing data
    existing_data = await redis_client.get(key)
    if existing_data:
      session_data = json.loads(existing_data)
    else:
      session_data = {}

    # Update with new data
    session_data.update(updates)

    # Store updated data
    serialized_data = json.dumps(session_data, default=str)

    if ttl:
      await redis_client.setex(key, ttl, serialized_data)
    else:
      await redis_client.set(key, serialized_data)

    logger.debug(f"Updated session data for call {call_id}")
    return True

  except Exception as e:
    logger.error(f"Failed to update session for call {call_id}: {e}")
    return False
