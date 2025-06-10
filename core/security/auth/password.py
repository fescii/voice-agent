"""
Password hashing utilities.
"""
import bcrypt
from typing import Optional
from core.config.registry import config_registry


class PasswordService:
  """Service for password hashing and verification."""

  def __init__(self):
    self.security_config = config_registry.security

  def hash_password(self, password: str) -> str:
    """
    Hash a password with bcrypt and salt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    # Combine password with salt
    salted_password = f"{password}{self.security_config.password_salt}"

    # Generate bcrypt hash
    hashed = bcrypt.hashpw(
        salted_password.encode('utf-8'),
        bcrypt.gensalt(rounds=self.security_config.password_rounds)
    )

    return hashed.decode('utf-8')

  def verify_password(self, password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        password: Plain text password
        hashed_password: Stored hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    try:
      # Combine password with salt
      salted_password = f"{password}{self.security_config.password_salt}"

      # Verify with bcrypt
      return bcrypt.checkpw(
          salted_password.encode('utf-8'),
          hashed_password.encode('utf-8')
      )
    except Exception:
      return False

  def generate_temp_password(self, length: int = 12) -> str:
    """
    Generate a temporary password.

    Args:
        length: Length of the password

    Returns:
        Temporary password string
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
