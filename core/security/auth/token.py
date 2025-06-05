"""
JWT token handling and API key validation
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from core.config.app.main import AppConfig


class TokenManager:
  """Handles JWT token operations"""

  def __init__(self):
    self.config = AppConfig()
    self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

  def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()

    if expires_delta:
      expire = datetime.utcnow() + expires_delta
    else:
      expire = datetime.utcnow() + timedelta(hours=24)

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, self.config.secret_key, algorithm="HS256")

  def verify_token(self, token: str) -> Dict[str, Any]:
    """Verify and decode JWT token"""
    try:
      payload = jwt.decode(token, self.config.secret_key, algorithms=["HS256"])
      return payload
    except jwt.PyJWTError:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Could not validate credentials"
      )

  def hash_password(self, password: str) -> str:
    """Hash password"""
    return self.pwd_context.hash(password)

  def verify_password(self, plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return self.pwd_context.verify(plain_password, hashed_password)


class APIKeyValidator:
  """Validates API keys for external services"""

  @staticmethod
  def validate_api_key(api_key: str, expected_prefix: str = "") -> bool:
    """Validate API key format and prefix"""
    if not api_key:
      return False

    if expected_prefix and not api_key.startswith(expected_prefix):
      return False

    return len(api_key) > 10  # Basic length check

  @staticmethod
  def validate_ringover_key(api_key: str) -> bool:
    """Validate Ringover API key"""
    return APIKeyValidator.validate_api_key(api_key)

  @staticmethod
  def validate_openai_key(api_key: str) -> bool:
    """Validate OpenAI API key"""
    return APIKeyValidator.validate_api_key(api_key, "sk-")

  @staticmethod
  def validate_elevenlabs_key(api_key: str) -> bool:
    """Validate ElevenLabs API key"""
    return APIKeyValidator.validate_api_key(api_key)


security = HTTPBearer()
token_manager = TokenManager()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
  """
  FastAPI dependency to get current authenticated user from JWT token

  Args:
      credentials: HTTP authorization credentials containing the JWT token

  Returns:
      User information from the token payload

  Raises:
      HTTPException: If token is invalid or expired
  """
  try:
    payload = token_manager.verify_token(credentials.credentials)
    user_id = payload.get("sub")

    if user_id is None:
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid token payload"
      )

    return payload

  except HTTPException:
    raise
  except Exception as e:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
  """
  FastAPI dependency to optionally get current authenticated user

  Args:
      credentials: Optional HTTP authorization credentials

  Returns:
      User information if authenticated, None otherwise
  """
  if credentials is None:
    return None

  try:
    return await get_current_user(credentials)
  except HTTPException:
    return None
