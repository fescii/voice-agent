"""
Read operations for users.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from typing import Optional, List, Union

from data.db.models.user import User, UserRole, UserStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_user_by_id(
    session: AsyncSession,
    user_id: Union[int, str]
) -> Optional[User]:
  """
  Get user by ID.

  Args:
    session: Database session
    user_id: User ID (int or str that can be converted to int)

  Returns:
    User object or None if not found
  """
  try:
    # Convert to int if it's a string
    if isinstance(user_id, str):
      user_id = int(user_id)

    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()
  except Exception as e:
    logger.error(f"Error getting user by ID {user_id}: {e}")
    return None


async def get_user_by_username(
    session: AsyncSession,
    username: str
) -> Optional[User]:
  """
  Get user by username.

  Args:
    session: Database session
    username: Username

  Returns:
    User object or None if not found
  """
  try:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()
  except Exception as e:
    logger.error(f"Error getting user by username {username}: {e}")
    return None


async def get_user_by_email(
    session: AsyncSession,
    email: str
) -> Optional[User]:
  """
  Get user by email.

  Args:
    session: Database session
    email: Email address

  Returns:
    User object or None if not found
  """
  try:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()
  except Exception as e:
    logger.error(f"Error getting user by email {email}: {e}")
    return None


async def get_user_by_api_key(
    session: AsyncSession,
    api_key_value: str
) -> Optional[User]:
  """
  Get user by API key.

  Args:
    session: Database session
    api_key_value: API key value

  Returns:
    User object or None if not found
  """
  try:
    if not api_key_value:
      return None
    # Use text() for the comparison to avoid type issues
    from sqlalchemy import text
    result = await session.execute(
        select(User).where(text("api_key = :api_key")
                           ).params(api_key=api_key_value)
    )
    return result.scalar_one_or_none()
  except Exception as e:
    logger.error(f"Error getting user by API key: {e}")
    return None


async def get_all_users(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    role: Optional[str] = None,
    active_only: bool = False
) -> List[User]:
  """
  Get all users with pagination and filtering.

  Args:
    session: Database session
    limit: Maximum number of users to return
    offset: Number of users to skip
    role: Filter by role (optional)
    active_only: Only return active users

  Returns:
    List of User objects
  """
  try:
    query = select(User)

    # Apply filters
    if active_only:
      query = query.where(User.status == UserStatus.ACTIVE)

    if role:
      from data.db.models.user import UserRole
      try:
        role_enum = UserRole(role)
        query = query.where(User.role == role_enum)
      except ValueError:
        logger.warning(f"Invalid role filter: {role}")

    # Apply pagination
    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    return list(result.scalars().all())
  except Exception as e:
    logger.error(f"Error getting all users: {e}")
    return []


async def get_users_by_role(
    session: AsyncSession,
    role: UserRole,
    limit: int = 100,
    offset: int = 0
) -> List[User]:
  """
  Get users by role.

  Args:
    session: Database session
    role: User role
    limit: Maximum number of users to return
    offset: Number of users to skip

  Returns:
    List of User objects
  """
  try:
    result = await session.execute(
        select(User).where(User.role == role).limit(limit).offset(offset)
    )
    return list(result.scalars().all())
  except Exception as e:
    logger.error(f"Error getting users by role {role}: {e}")
    return []


async def get_active_users(
    session: AsyncSession,
    limit: int = 100,
    offset: int = 0
) -> List[User]:
  """
  Get active users.

  Args:
    session: Database session
    limit: Maximum number of users to return
    offset: Number of users to skip

  Returns:
    List of active User objects
  """
  try:
    result = await session.execute(
        select(User).where(
            User.status == UserStatus.ACTIVE,
            User.email_verified == True
        ).limit(limit).offset(offset)
    )
    return list(result.scalars().all())
  except Exception as e:
    logger.error(f"Error getting active users: {e}")
    return []
