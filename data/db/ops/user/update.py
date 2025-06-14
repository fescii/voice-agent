"""
Update operations for users.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import update, select
from typing import Optional, Dict, Any, Union
from datetime import datetime, timezone

from data.db.models.user import User, UserStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


def _convert_user_id(user_id: Union[str, int]) -> int:
  """Convert user_id to integer if it's a string."""
  if isinstance(user_id, str):
    return int(user_id)
  return user_id


async def update_user(
    session: AsyncSession,
    user_id: str,
    **kwargs
) -> Optional[User]:
  """
  Update user information.

  Args:
    session: Database session
    user_id: User ID
    **kwargs: Fields to update

  Returns:
    Updated User object or None if failed
  """
  try:
    # Convert user_id to integer
    user_id_int = _convert_user_id(user_id)

    # Update the user
    await session.execute(
        update(User)
        .where(User.id == user_id_int)
        .values(**kwargs)
    )
    await session.commit()

    # Return updated user
    result = await session.execute(
        select(User).where(User.id == user_id_int)
    )
    user = result.scalar_one_or_none()

    if user:
      logger.info(f"Updated user: {user.username}")

    return user

  except ValueError as e:
    logger.error(f"Invalid user ID format {user_id}: {e}")
    return None

  except SQLAlchemyError as e:
    logger.error(f"Failed to update user {user_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error updating user {user_id}: {e}")
    await session.rollback()
    return None


async def update_user_password(
    session: AsyncSession,
    user_id: str,
    new_password: str
) -> bool:
  """
  Update user password.

  Args:
    session: Database session
    user_id: User ID
    new_password: New password (plain text, will be hashed)

  Returns:
    True if successful, False otherwise
  """
  try:
    # Convert user_id to integer
    user_id_int = _convert_user_id(user_id)

    # Get the user
    result = await session.execute(
        select(User).where(User.id == user_id_int)
    )
    user = result.scalar_one_or_none()

    if not user:
      logger.error(f"User {user_id} not found")
      return False

    # Update password
    user.set_password(new_password)
    await session.commit()

    logger.info(f"Password updated for user: {user_id}")
    return True

  except ValueError as e:
    logger.error(f"Invalid user ID format {user_id}: {e}")
    return False
  except SQLAlchemyError as e:
    logger.error(f"Failed to update password for user {user_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Error updating password for user {user_id}: {e}")
    await session.rollback()
    return False


async def update_last_login(
    session: AsyncSession,
    user_id: str,
    login_time: Optional[datetime] = None
) -> bool:
  """
  Update user's last login time.

  Args:
    session: Database session
    user_id: User ID
    login_time: Login time (default: current time)

  Returns:
    True if successful, False otherwise
  """
  try:
    if login_time is None:
      login_time = datetime.now(timezone.utc)

    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            last_login=login_time,
            last_activity=login_time,
            failed_login_attempts="0"  # Reset failed attempts on successful login
        )
    )
    await session.commit()
    return True

  except Exception as e:
    logger.error(f"Error updating last login for user {user_id}: {e}")
    await session.rollback()
    return False


async def increment_failed_login_attempts(
    session: AsyncSession,
    user_id: str
) -> bool:
  """
  Increment failed login attempts counter.

  Args:
    session: Database session
    user_id: User ID

  Returns:
    True if successful, False otherwise
  """
  try:
    # Get current failed attempts
    result = await session.execute(
        select(User.failed_login_attempts).where(User.id == user_id)
    )
    current_attempts = result.scalar_one_or_none()

    if current_attempts is None:
      return False

    # Increment attempts
    new_attempts = str(int(current_attempts) + 1)

    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(failed_login_attempts=new_attempts)
    )
    await session.commit()
    return True

  except Exception as e:
    logger.error(
        f"Error incrementing failed login attempts for user {user_id}: {e}")
    await session.rollback()
    return False


async def verify_email(
    session: AsyncSession,
    user_id: str
) -> bool:
  """
  Mark user's email as verified.

  Args:
    session: Database session
    user_id: User ID

  Returns:
    True if successful, False otherwise
  """
  try:
    await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(
            email_verified=True,
            email_verification_token=None
        )
    )
    await session.commit()

    logger.info(f"Email verified for user {user_id}")
    return True

  except Exception as e:
    logger.error(f"Error verifying email for user {user_id}: {e}")
    await session.rollback()
    return False


async def update_user_last_login(
    session: AsyncSession,
    user_id: str
) -> bool:
  """
  Update user's last login timestamp.

  Args:
      session: Database session
      user_id: User ID to update

  Returns:
      True if successful, False otherwise
  """
  try:
    # Convert string ID to integer
    user_id_int = _convert_user_id(user_id)

    stmt = update(User).where(User.id == user_id_int).values(
        last_login=datetime.now()  # Use timezone-naive datetime
    )
    await session.execute(stmt)
    await session.commit()
    logger.info(f"Updated last login for user: {user_id}")
    return True

  except ValueError as e:
    logger.error(f"Invalid user ID format {user_id}: {e}")
    return False
  except SQLAlchemyError as e:
    logger.error(f"Failed to update last login for user {user_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(
        f"Unexpected error updating last login for user {user_id}: {e}")
    await session.rollback()
    return False


async def update_user_profile(
    session: AsyncSession,
    user_id: str,
    **kwargs
) -> bool:
  """
  Update user profile information.

  Args:
      session: Database session
      user_id: User ID to update
      **kwargs: Fields to update

  Returns:
      True if successful, False otherwise
  """
  try:
    # Remove None values
    update_data = {k: v for k, v in kwargs.items() if v is not None}

    if not update_data:
      return True  # Nothing to update

    stmt = update(User).where(User.id == user_id).values(**update_data)
    await session.execute(stmt)
    await session.commit()
    logger.info(f"Updated profile for user: {user_id}")
    return True

  except SQLAlchemyError as e:
    logger.error(f"Failed to update profile for user {user_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error updating profile for user {user_id}: {e}")
    await session.rollback()
    return False


async def update_user_status(
    session: AsyncSession,
    user_id: str,
    is_active: Optional[bool] = None,
    is_verified: Optional[bool] = None
) -> bool:
  """
  Update user status flags.

  Args:
      session: Database session
      user_id: User ID to update
      is_active: Active status (converted to UserStatus.ACTIVE/INACTIVE)
      is_verified: Verified status (email_verified field)

  Returns:
      True if successful, False otherwise
  """
  try:
    update_data = {}

    if is_active is not None:
      # Convert boolean to UserStatus enum
      update_data["status"] = UserStatus.ACTIVE if is_active else UserStatus.INACTIVE

    if is_verified is not None:
      update_data["email_verified"] = is_verified

    if not update_data:
      return True  # Nothing to update

    stmt = update(User).where(User.id == user_id).values(**update_data)
    result = await session.execute(stmt)
    await session.commit()

    return result.rowcount > 0

  except SQLAlchemyError as e:
    logger.error(f"Failed to update user status {user_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error updating status for user {user_id}: {e}")
    await session.rollback()
    return False
