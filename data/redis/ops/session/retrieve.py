"""
Retrieve call session state from Redis.
"""
import json
from typing import Dict, Any, Optional
from ...connection import get_redis_client
from ....core.logging import get_logger

logger = get_logger(__name__)


async def get_call_session(call_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve call session data from Redis.
    
    Args:
        call_id: Call identifier
        
    Returns:
        Session data dict or None if not found
    """
    try:
        redis_client = await get_redis_client()
        key = f"call_session:{call_id}"
        
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to retrieve session for call {call_id}: {e}")
        return None


async def get_session_field(call_id: str, field: str) -> Optional[Any]:
    """
    Get a specific field from call session data.
    
    Args:
        call_id: Call identifier
        field: Field name to retrieve
        
    Returns:
        Field value or None if not found
    """
    try:
        session_data = await get_call_session(call_id)
        if session_data:
            return session_data.get(field)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to get session field {field} for call {call_id}: {e}")
        return None
