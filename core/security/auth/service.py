"""
Authentication service for login/logout functionality.
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from data.db.connection import get_db_session
from data.db.models.user import User, UserStatus
from data.db.ops.user.read import get_user_by_email, get_user_by_id
from data.db.ops.user.update import update_user_last_login, update_user_password
from .password import PasswordService
from .jwt import TokenService
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AuthService:
  """Service for user authentication operations."""

  def __init__(self):
    self.password_service = PasswordService()
    self.token_service = TokenService()

  async def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user with email and password.

    Args:
        email: User email
        password: User password

    Returns:
        Authentication result with tokens if successful, None if failed
    """
    try:
      async with get_db_session() as session:
        # Get user by email
        user = await get_user_by_email(session, email)

        if not user:
          logger.warning(f"Login attempt with unknown email: {email}")
          return None

        # Check if user is active - get the actual value from the user object
        user_status = getattr(user, 'status', None)
        logger.info(
            f"User {email} found with status: {user_status}, email_verified: {getattr(user, 'email_verified', None)}")
        if not user_status or user_status != UserStatus.ACTIVE:
          logger.warning(
              f"Login attempt with inactive user: {email} (status: {user_status})")
          return None

        # Verify password using the user's own verification method
        logger.info(
            f"Verifying password for user: {email}, has password_hash: {bool(user.password_hash)}, has salt: {bool(user.salt)}")
        password_valid = user.verify_password(password)
        logger.info(
            f"Password verification result for {email}: {password_valid}")
        if not password_valid:
          logger.warning(f"Invalid password for user: {email}")
          return None

        # Update last login
        await update_user_last_login(session, str(user.id))

        # Generate tokens
        access_token = self.token_service.create_access_token(
            user_id=str(user.id),
            email=str(user.email),
            role=user.role.value,
            full_name=str(user.full_name or "")
        )

        refresh_token = self.token_service.create_refresh_token(
            user_id=str(user.id),
            email=str(user.email)
        )

        logger.info(f"Successful login for user: {email}")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": str(user.email),
                "full_name": str(user.full_name or ""),
                "role": user.role.value,
                "is_active": getattr(user, 'status', None) == UserStatus.ACTIVE
            }
        }

    except Exception as e:
      logger.error(f"Login error for {email}: {e}")
      return None

  async def logout(self, user_id: str) -> bool:
    """
    Logout user (in a full implementation, this would invalidate tokens).

    Args:
        user_id: User ID

    Returns:
        True if successful
    """
    try:
      # In a full implementation, you might:
      # 1. Add token to blacklist
      # 2. Update user's last_logout timestamp
      # 3. Clear session data

      logger.info(f"User logged out: {user_id}")
      return True

    except Exception as e:
      logger.error(f"Logout error for user {user_id}: {e}")
      return False

  async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
    """
    Refresh access token using refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        New access token if successful, None if failed
    """
    try:
      # Validate refresh token
      payload = self.token_service.validate_token(refresh_token)

      if not payload or payload.get("type") != "refresh":
        logger.warning("Invalid refresh token")
        return None

      # Get user to ensure they still exist and are active
      async with get_db_session() as session:
        user = await get_user_by_id(session, payload["sub"])

        if not user or getattr(user, 'status', None) != UserStatus.ACTIVE:
          logger.warning(
              f"Refresh token for inactive/missing user: {payload['sub']}")
          return None

        # Create new access token
        access_token = self.token_service.create_access_token(
            user_id=str(user.id),
            email=str(user.email),
            role=user.role.value,
            full_name=str(user.full_name or "")
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except Exception as e:
      logger.error(f"Token refresh error: {e}")
      return None

  async def validate_user_token(self, token: str) -> Optional[Dict[str, Any]]:
    """
    Validate user token and return user info.

    Args:
        token: JWT access token

    Returns:
        User info if token is valid, None otherwise
    """
    try:
      # Validate token
      payload = self.token_service.validate_token(token)

      if not payload or payload.get("type") != "access":
        return None

      # Get user to ensure they still exist and are active
      async with get_db_session() as session:
        user = await get_user_by_id(session, payload["sub"])

        if not user or getattr(user, 'status', None) != UserStatus.ACTIVE:
          return None

        return {
            "user_id": str(user.id),
            "email": str(user.email),
            "full_name": str(user.full_name or ""),
            "role": user.role.value,
            "is_active": getattr(user, 'status', None) == UserStatus.ACTIVE
        }

    except Exception as e:
      logger.error(f"Token validation error: {e}")
      return None

  async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
    """
    Change user password.

    Args:
        user_id: User ID
        old_password: Current password
        new_password: New password

    Returns:
        True if successful, False otherwise
    """
    try:
      async with get_db_session() as session:
        # Convert user_id to int and get user
        user = await get_user_by_id(session, int(user_id))

        if not user:
          return False

        # Verify old password using user's verification method
        if not user.verify_password(old_password):
          return False

        # Set new password using user's method (will handle hashing)
        user.set_password(new_password)

        # Commit the changes
        await session.commit()

        logger.info(f"Password changed for user: {user_id}")
        return True

    except Exception as e:
      logger.error(f"Password change error for user {user_id}: {e}")
      return False
