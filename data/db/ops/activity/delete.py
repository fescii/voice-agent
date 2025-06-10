"""
Delete operations for activities.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from data.db.models.activity import Activity
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def delete_activity(
    session: AsyncSession,
    activity_id: str
) -> bool:
  """
  Delete activity by ID.

  Args:
      session: Database session
      activity_id: Activity ID

  Returns:
      True if deleted successfully, False otherwise
  """
  try:
    # Check if activity exists first
    stmt = select(Activity).where(Activity.id == activity_id)
    result = await session.execute(stmt)
    activity = result.scalar_one_or_none()

    if not activity:
      logger.warning(f"Activity not found for deletion: {activity_id}")
      return False

    # Delete the activity
    stmt = delete(Activity).where(Activity.id == activity_id)
    await session.execute(stmt)
    await session.commit()

    logger.info(f"Deleted activity: {activity_id}")
    return True

  except SQLAlchemyError as e:
    logger.error(f"Failed to delete activity {activity_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error deleting activity {activity_id}: {e}")
    await session.rollback()
    return False
