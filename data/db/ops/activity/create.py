"""
Create operations for activities.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from data.db.models.activity import Activity, ActivityType, ActivityStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def create_activity(
    session: AsyncSession,
    activity_type: ActivityType,
    subject: str,
    owner_id: str,
    **kwargs
) -> Optional[Activity]:
  """
  Create a new activity record.

  Args:
      session: Database session
      activity_type: Type of activity (required)
      subject: Activity subject (required)
      owner_id: Owner/performer ID (required)
      **kwargs: Additional activity fields

  Returns:
      Created Activity object or None if failed
  """
  try:
    activity = Activity(
        activity_type=activity_type,
        subject=subject,
        owner_id=owner_id,
        **kwargs
    )

    session.add(activity)
    await session.commit()
    await session.refresh(activity)

    logger.info(f"Created activity: {activity.id} - {subject}")
    return activity

  except SQLAlchemyError as e:
    logger.error(f"Failed to create activity {subject}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error creating activity {subject}: {e}")
    await session.rollback()
    return None
