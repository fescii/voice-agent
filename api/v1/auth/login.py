"""
Login and logout API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any

from api.v1.schemas.auth.login import (
    LoginRequest, LoginResponse, RefreshTokenRequest, RefreshTokenResponse,
    LogoutRequest, ChangePasswordRequest, MessageResponse
)
from core.security.auth.service import AuthService
from core.logging.setup import get_logger

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
logger = get_logger(__name__)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
  """
  Authenticate user with email and password.

  Returns JWT access and refresh tokens on successful authentication.
  """
  auth_service = AuthService()

  result = await auth_service.login(request.email, request.password)

  if not result:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )

  return LoginResponse(**result)


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
  """
  Refresh access token using valid refresh token.
  """
  auth_service = AuthService()

  result = await auth_service.refresh_token(request.refresh_token)

  if not result:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token"
    )

  return RefreshTokenResponse(**result)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Logout user and invalidate tokens.
  """
  auth_service = AuthService()

  # Validate current token to get user ID
  user_info = await auth_service.validate_user_token(credentials.credentials)

  if not user_info:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

  success = await auth_service.logout(user_info["user_id"])

  if not success:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Logout failed"
    )

  return MessageResponse(message="Successfully logged out")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Change user password.
  """
  auth_service = AuthService()

  # Validate current token to get user ID
  user_info = await auth_service.validate_user_token(credentials.credentials)

  if not user_info:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

  success = await auth_service.change_password(
      user_info["user_id"],
      request.old_password,
      request.new_password
  )

  if not success:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Failed to change password. Check your current password."
    )

  return MessageResponse(message="Password changed successfully")


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Get current user information from token.
  """
  auth_service = AuthService()

  user_info = await auth_service.validate_user_token(credentials.credentials)

  if not user_info:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

  return user_info
