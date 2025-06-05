"""
Delete operations for call logs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError

from data.db.models.calllog import CallLog
from core.logging import get_logger

logger = get_logger(__name__)


async def delete_call_log(session: AsyncSession, call_id: str) -> bool:
  """
  Delete call log by call ID.

  Args:
      session: Database session
      call_id: Call identifier

  Returns:
      True if deletion was successful
  """
  try:
    result = await session.execute(
        delete(CallLog).where(CallLog.call_id == call_id)
    )

    await session.commit()

    if result.rowcount > 0:
      logger.info(f"Deleted call log {call_id}")
      return True
    else:
      logger.warning(f"No call found with ID {call_id} to delete")
      return False

  except SQLAlchemyError as e:
    logger.error(f"Failed to delete call log {call_id}: {e}")
    await session.rollback()
    return False
