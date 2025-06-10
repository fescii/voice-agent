"""
JWT token service for authentication.
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from core.config.registry import config_registry
from core.logging.setup import get_logger

logger = get_logger(__name__)


class TokenService:
  """Service for JWT token generation and validation."""

  def __init__(self):
    self.security_config = config_registry.security

  def create_access_token(self, user_id: str, email: str, role: str, **kwargs) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User ID
        email: User email
        role: User role
        **kwargs: Additional claims

    Returns:
        JWT token string
    """
    now = datetime.now(timezone.utc)
    expires = now + \
        timedelta(minutes=self.security_config.jwt_access_token_expire_minutes)

    payload = {
        "sub": user_id,  # Subject (user ID)
        "email": email,
        "role": role,
        "type": "access",
        "iat": now.timestamp(),  # Issued at
        "exp": expires.timestamp(),  # Expires
        "iss": "voice-agent-system",  # Issuer
        **kwargs  # Additional claims
    }

    return jwt.encode(
        payload,
        self.security_config.jwt_secret_key,
        algorithm=self.security_config.jwt_algorithm
    )

  def create_refresh_token(self, user_id: str, email: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User ID
        email: User email

    Returns:
        JWT refresh token string
    """
    now = datetime.now(timezone.utc)
    expires = now + \
        timedelta(days=self.security_config.jwt_refresh_token_expire_days)

    payload = {
        "sub": user_id,
        "email": email,
        "type": "refresh",
        "iat": now.timestamp(),
        "exp": expires.timestamp(),
        "iss": "voice-agent-system"
    }

    return jwt.encode(
        payload,
        self.security_config.jwt_secret_key,
        algorithm=self.security_config.jwt_algorithm
    )

  def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
    """
    Validate and decode a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
      payload = jwt.decode(
          token,
          self.security_config.jwt_secret_key,
          algorithms=[self.security_config.jwt_algorithm]
      )

      # Check if token is expired
      now = datetime.now(timezone.utc).timestamp()
      if payload.get("exp", 0) < now:
        logger.warning("Token has expired")
        return None

      return payload

    except jwt.ExpiredSignatureError:
      logger.warning("Token has expired")
      return None
    except jwt.InvalidTokenError as e:
      logger.warning(f"Invalid token: {e}")
      return None
    except Exception as e:
      logger.error(f"Token validation error: {e}")
      return None

  def refresh_access_token(self, refresh_token: str) -> Optional[str]:
    """
    Create a new access token from a valid refresh token.

    Args:
        refresh_token: Valid refresh token

    Returns:
        New access token if refresh token is valid, None otherwise
    """
    payload = self.validate_token(refresh_token)

    if not payload:
      return None

    if payload.get("type") != "refresh":
      logger.warning("Token is not a refresh token")
      return None

    # Create new access token (would need to fetch user role from database)
    return self.create_access_token(
        user_id=payload["sub"],
        email=payload["email"],
        role="user"  # Would fetch from database in real implementation
    )

  def extract_user_from_token(self, token: str) -> Optional[Dict[str, str]]:
    """
    Extract user information from a valid token.

    Args:
        token: JWT token string

    Returns:
        User info dict if valid, None otherwise
    """
    payload = self.validate_token(token)

    if not payload:
      return None

    return {
        "user_id": payload["sub"],
        "email": payload["email"],
        "role": payload.get("role", "user")
    }
