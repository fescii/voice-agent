"""
Read operations for activities.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from data.db.models.activity import Activity
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_activity(
    session: AsyncSession,
    activity_id: str
) -> Optional[Activity]:
  """
  Get activity by ID.

  Args:
      session: Database session
      activity_id: Activity ID

  Returns:
      Activity object or None if not found
  """
  try:
    stmt = select(Activity).where(Activity.id == activity_id)
    result = await session.execute(stmt)
    activity = result.scalar_one_or_none()

    if activity:
      logger.debug(f"Found activity: {activity_id}")
    else:
      logger.debug(f"Activity not found: {activity_id}")

    return activity

  except SQLAlchemyError as e:
    logger.error(f"Failed to get activity {activity_id}: {e}")
    return None


async def get_activities_by_contact(
    session: AsyncSession,
    contact_id: str
) -> List[Activity]:
  """
  Get activities by contact ID.

  Args:
      session: Database session
      contact_id: Contact ID

  Returns:
      List of Activity objects
  """
  try:
    stmt = select(Activity).where(Activity.contact_id == contact_id)
    result = await session.execute(stmt)
    activities = result.scalars().all()

    logger.debug(
        f"Found {len(activities)} activities for contact: {contact_id}")
    return list(activities)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get activities by contact {contact_id}: {e}")
    return []
