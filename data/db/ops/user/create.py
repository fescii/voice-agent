"""
Create operations for users.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from data.db.models.user import User, UserRole, UserStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def create_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole = UserRole.USER,
    **kwargs
) -> Optional[User]:
  """
  Create a new user.

  Args:
    session: Database session
    username: Unique username
    email: Unique email address
    password: Plain text password (will be hashed)
    first_name: User's first name
    last_name: User's last name
    role: User role (default: USER)
    **kwargs: Additional user fields

  Returns:
    Created User object or None if failed
  """
  try:
    # Check if username or email already exists
    existing_user = await session.execute(
        select(User).where(
            (User.username == username) | (User.email == email)
        )
    )
    if existing_user.scalar_one_or_none():
      logger.error(
          f"User with username '{username}' or email '{email}' already exists")
      return None

    # Create user instance
    user = User(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        full_name=f"{first_name} {last_name}",
        role=role,
        status=UserStatus.PENDING,  # Require email verification
        **kwargs
    )

    # Set password (will be hashed automatically)
    user.set_password(password)

    # Generate API key
    user.generate_api_key()

    session.add(user)
    await session.commit()
    await session.refresh(user)

    logger.info(f"Created user: {username} ({email})")
    return user

  except SQLAlchemyError as e:
    logger.error(f"Failed to create user {username}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error creating user {username}: {e}")
    await session.rollback()
    return None


async def create_admin_user(
    session: AsyncSession,
    username: str,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    **kwargs
) -> Optional[User]:
  """
  Create an admin user with admin role and active status.

  Args:
    session: Database session
    username: Unique username
    email: Unique email address
    password: Plain text password (will be hashed)
    first_name: User's first name
    last_name: User's last name
    **kwargs: Additional user fields

  Returns:
    Created User object or None if failed
  """
  return await create_user(
      session=session,
      username=username,
      email=email,
      password=password,
      first_name=first_name,
      last_name=last_name,
      role=UserRole.ADMIN,
      status=UserStatus.ACTIVE,
      email_verified=True,
      **kwargs
  )
