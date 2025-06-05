"""
Read operations for call logs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any

from ...models.calllog import CallLog, CallStatus
from ....core.logging import get_logger

logger = get_logger(__name__)


async def get_call_log(session: AsyncSession, call_id: str) -> Optional[CallLog]:
  """
  Get call log by call ID.

  Args:
      session: Database session
      call_id: Call identifier

  Returns:
      CallLog instance or None if not found
  """
  try:
    result = await session.execute(
        select(CallLog).where(CallLog.call_id == call_id)
    )
    return result.scalar_one_or_none()

  except SQLAlchemyError as e:
    logger.error(f"Failed to get call log {call_id}: {e}")
    return None


async def get_call_by_ringover_id(
    session: AsyncSession,
    ringover_call_id: str
) -> Optional[CallLog]:
  """
  Get call log by Ringover call ID.

  Args:
      session: Database session
      ringover_call_id: Ringover call identifier

  Returns:
      CallLog instance or None if not found
  """
  try:
    result = await session.execute(
        select(CallLog).where(CallLog.ringover_call_id == ringover_call_id)
    )
    return result.scalar_one_or_none()

  except SQLAlchemyError as e:
    logger.error(
        f"Failed to get call log by Ringover ID {ringover_call_id}: {e}")
    return None


async def get_call_logs(
    session: AsyncSession,
    agent_id: Optional[str] = None,
    status: Optional[CallStatus] = None,
    limit: int = 100,
    offset: int = 0
) -> List[CallLog]:
  """
  Get call logs with optional filtering.

  Args:
      session: Database session
      agent_id: Filter by agent ID
      status: Filter by call status
      limit: Maximum number of results
      offset: Offset for pagination

  Returns:
      List of CallLog instances
  """
  try:
    query = select(CallLog)

    if agent_id:
      query = query.where(CallLog.agent_id == agent_id)
    if status:
      query = query.where(CallLog.status == status)

    query = query.limit(limit).offset(
        offset).order_by(CallLog.created_at.desc())

    result = await session.execute(query)
    return result.scalars().all()

  except SQLAlchemyError as e:
    logger.error(f"Failed to get call logs: {e}")
    return []
