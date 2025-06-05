"""
Update call session data in Redis.
"""
from typing import Dict, Any, Optional
from data.redis.connection import get_redis_client
from core.logging import get_logger

logger = get_logger(__name__)


async def update_call_session(call_id: str, session_data: Dict[str, Any]) -> bool:
  """
  Update call session data in Redis.

  Args:
      call_id: Call identifier
      session_data: Session data to update

  Returns:
      True if update was successful, False otherwise
  """
  try:
    redis_client = await get_redis_client()
    session_key = f"call_session:{call_id}"

    # Update the session data
    redis_client.hmset(session_key, session_data)

    logger.debug(f"Updated call session for {call_id}")
    return True

  except Exception as e:
    logger.error(f"Failed to update call session {call_id}: {e}")
    return False


async def update_call_session_field(call_id: str, field: str, value: Any) -> bool:
  """
  Update a specific field in call session data.

  Args:
      call_id: Call identifier
      field: Field name to update
      value: New value for the field

  Returns:
      True if update was successful, False otherwise
  """
  try:
    redis_client = await get_redis_client()
    session_key = f"call_session:{call_id}"

    # Update the specific field
    redis_client.hset(session_key, field, str(value))

    logger.debug(f"Updated field {field} for call session {call_id}")
    return True

  except Exception as e:
    logger.error(
        f"Failed to update field {field} for call session {call_id}: {e}")
    return False
