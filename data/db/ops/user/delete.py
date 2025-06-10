"""
Delete operations for users.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete, select
from typing import Optional

from data.db.models.user import User
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def delete_user(
    session: AsyncSession,
    user_id: str
) -> bool:
  """
  Delete a user (hard delete).

  Args:
    session: Database session
    user_id: User ID

  Returns:
    True if successful, False otherwise
  """
  try:
    # Check if user exists first
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
      logger.warning(f"User {user_id} not found for deletion")
      return False

    username = user.username

    # Delete the user
    await session.execute(
        delete(User).where(User.id == user_id)
    )
    await session.commit()

    logger.info(f"Deleted user: {username} ({user_id})")
    return True

  except SQLAlchemyError as e:
    logger.error(f"Failed to delete user {user_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error deleting user {user_id}: {e}")
    await session.rollback()
    return False


async def soft_delete_user(
    session: AsyncSession,
    user_id: str
) -> bool:
  """
  Soft delete a user (mark as inactive).

  Args:
    session: Database session
    user_id: User ID

  Returns:
    True if successful, False otherwise
  """
  try:
    from data.db.models.user import UserStatus
    from sqlalchemy import update

    # Update user status to inactive
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(status=UserStatus.INACTIVE)
    )
    await session.commit()

    logger.info(f"Soft deleted user: {user_id}")
    return True

  except Exception as e:
    logger.error(f"Error soft deleting user {user_id}: {e}")
    await session.rollback()
    return False
