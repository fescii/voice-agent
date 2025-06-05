"""
Update operations for call logs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any
from datetime import datetime

from data.db.models.calllog import CallLog, CallStatus
from core.logging import get_logger

logger = get_logger(__name__)


async def update_call_status(
    session: AsyncSession,
    call_id: str,
    status: CallStatus,
    **kwargs
) -> bool:
  """
  Update call status and related timing fields.

  Args:
      session: Database session
      call_id: Call identifier
      status: New call status
      **kwargs: Additional fields to update

  Returns:
      True if update was successful
  """
  try:
    update_data = {"status": status, "updated_at": datetime.utcnow()}

    # Add timing fields based on status
    if status == CallStatus.ANSWERED:
      update_data["answered_at"] = datetime.utcnow()
    elif status in [CallStatus.COMPLETED, CallStatus.FAILED, CallStatus.TERMINATED]:
      update_data["ended_at"] = datetime.utcnow()

    # Add any additional fields
    update_data.update(kwargs)

    result = await session.execute(
        update(CallLog)
        .where(CallLog.call_id == call_id)
        .values(**update_data)
    )

    await session.commit()

    if result.rowcount > 0:
      logger.info(f"Updated call {call_id} status to {status}")
      return True
    else:
      logger.warning(f"No call found with ID {call_id} to update")
      return False

  except SQLAlchemyError as e:
    logger.error(f"Failed to update call status for {call_id}: {e}")
    await session.rollback()
    return False


async def update_call_log(
    session: AsyncSession,
    call_id: str,
    **kwargs
) -> bool:
  """
  Update call log with arbitrary fields.

  Args:
      session: Database session
      call_id: Call identifier
      **kwargs: Fields to update

  Returns:
      True if update was successful
  """
  try:
    if not kwargs:
      return True

    update_data = {**kwargs, "updated_at": datetime.utcnow()}

    result = await session.execute(
        update(CallLog)
        .where(CallLog.call_id == call_id)
        .values(**update_data)
    )

    await session.commit()

    if result.rowcount > 0:
      logger.info(f"Updated call log {call_id}")
      return True
    else:
      logger.warning(f"No call found with ID {call_id} to update")
      return False

  except SQLAlchemyError as e:
    logger.error(f"Failed to update call log {call_id}: {e}")
    await session.rollback()
    return False
