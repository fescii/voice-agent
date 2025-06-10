"""
Authentication dependencies for FastAPI endpoints.
"""
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

from core.security.auth.service import AuthService
from data.db.models.user import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
  """
  Get current authenticated user from JWT token.

  Returns:
      User information dict

  Raises:
      HTTPException: If token is invalid or user not found
  """
  auth_service = AuthService()

  user_info = await auth_service.validate_user_token(credentials.credentials)

  if not user_info:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

  return user_info


async def require_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
  """
  Require admin role for the current user.

  Args:
      current_user: Current authenticated user

  Returns:
      User information dict

  Raises:
      HTTPException: If user is not admin
  """
  if current_user["role"] not in ["admin", "super_admin"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required"
    )

  return current_user


async def require_super_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
  """
  Require super admin role for the current user.

  Args:
      current_user: Current authenticated user

  Returns:
      User information dict

  Raises:
      HTTPException: If user is not super admin
  """
  if current_user["role"] != "super_admin":
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Super admin access required"
    )

  return current_user


async def require_agent_or_admin(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
  """
  Require agent or admin role for the current user.

  Args:
      current_user: Current authenticated user

  Returns:
      User information dict

  Raises:
      HTTPException: If user is not agent or admin
  """
  if current_user["role"] not in ["agent", "admin", "super_admin"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Agent or admin access required"
    )

  return current_user


def require_role(required_role: str):
  """
  Create a dependency that requires a specific role.

  Args:
      required_role: The role required to access the endpoint

  Returns:
      FastAPI dependency function
  """
  async def check_role(
      current_user: Dict[str, Any] = Depends(get_current_user)
  ) -> Dict[str, Any]:
    if current_user["role"] != required_role:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail=f"Role '{required_role}' required"
      )
    return current_user

  return check_role
