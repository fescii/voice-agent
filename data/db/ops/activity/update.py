"""
Update operations for activities.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime, timezone

from data.db.models.activity import Activity, ActivityStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def update_activity(
    session: AsyncSession,
    activity_id: str,
    **kwargs
) -> Optional[Activity]:
  """
  Update activity information.

  Args:
      session: Database session
      activity_id: Activity ID
      **kwargs: Fields to update

  Returns:
      Updated Activity object or None if failed
  """
  try:
    # Add updated timestamp
    kwargs["updated_at"] = datetime.now(timezone.utc)

    stmt = update(Activity).where(Activity.id == activity_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()

    # Get updated activity
    stmt = select(Activity).where(Activity.id == activity_id)
    result = await session.execute(stmt)
    updated_activity = result.scalar_one_or_none()

    if updated_activity:
      logger.info(f"Updated activity: {activity_id}")
      return updated_activity
    else:
      logger.warning(f"Activity not found for update: {activity_id}")
      return None

  except SQLAlchemyError as e:
    logger.error(f"Failed to update activity {activity_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error updating activity {activity_id}: {e}")
    await session.rollback()
    return None


async def complete_activity(
    session: AsyncSession,
    activity_id: str,
    outcome: Optional[str] = None,
    **kwargs
) -> Optional[Activity]:
  """
  Mark activity as completed.

  Args:
      session: Database session
      activity_id: Activity ID
      outcome: Activity outcome/result
      **kwargs: Additional fields to update

  Returns:
      Updated Activity object or None if failed
  """
  try:
    update_data = {
        "status": ActivityStatus.COMPLETED,
        "completed_at": datetime.now(timezone.utc),
        **kwargs
    }

    if outcome:
      update_data["outcome"] = outcome

    return await update_activity(session, activity_id, **update_data)

  except Exception as e:
    logger.error(f"Unexpected error completing activity {activity_id}: {e}")
    return None
