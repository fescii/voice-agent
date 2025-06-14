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
from core.config.response import GenericResponse
from core.security.auth.service import AuthService
from core.logging.setup import get_logger

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()
logger = get_logger(__name__)


@router.post("/login", response_model=GenericResponse[LoginResponse])
async def login(request: LoginRequest):
  """
  Authenticate user with email and password.

  Returns JWT access and refresh tokens on successful authentication.
  """
  try:
    auth_service = AuthService()

    result = await auth_service.login(request.email, request.password)

    if not result:
      return GenericResponse.error(
          message="Invalid email or password",
          status_code=401
      )

    login_response = LoginResponse(**result)
    return GenericResponse.ok(
        data=login_response,
        status_code=200
    )

  except Exception as e:
    logger.error(f"Login error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred during login",
        details=str(e),
        status_code=500
    )


@router.post("/refresh", response_model=GenericResponse[RefreshTokenResponse])
async def refresh_token(request: RefreshTokenRequest):
  """
  Refresh access token using valid refresh token.
  """
  try:
    auth_service = AuthService()

    result = await auth_service.refresh_token(request.refresh_token)

    if not result:
      return GenericResponse.error(
          message="Invalid or expired refresh token",
          status_code=401
      )

    refresh_response = RefreshTokenResponse(**result)
    return GenericResponse.ok(
        data=refresh_response,
        status_code=200
    )

  except Exception as e:
    logger.error(f"Token refresh error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred during token refresh",
        details=str(e),
        status_code=500
    )


@router.post("/logout", response_model=GenericResponse[MessageResponse])
async def logout(
    request: LogoutRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Logout user and invalidate tokens.
  """
  try:
    auth_service = AuthService()

    # Validate current token to get user ID
    user_info = await auth_service.validate_user_token(credentials.credentials)

    if not user_info:
      return GenericResponse.error(
          message="Invalid token",
          status_code=401
      )

    success = await auth_service.logout(user_info["user_id"])

    if not success:
      return GenericResponse.error(
          message="Logout failed",
          status_code=500
      )

    message_response = MessageResponse(message="Successfully logged out")
    return GenericResponse.ok(
        data=message_response,
        status_code=200
    )

  except Exception as e:
    logger.error(f"Logout error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred during logout",
        details=str(e),
        status_code=500
    )


@router.post("/change-password", response_model=GenericResponse[MessageResponse])
async def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Change user password.
  """
  try:
    auth_service = AuthService()

    # Validate current token to get user ID
    user_info = await auth_service.validate_user_token(credentials.credentials)

    if not user_info:
      return GenericResponse.error(
          message="Invalid token",
          status_code=401
      )

    success = await auth_service.change_password(
        user_info["user_id"],
        request.old_password,
        request.new_password
    )

    if not success:
      return GenericResponse.error(
          message="Failed to change password. Check your current password.",
          status_code=400
      )

    message_response = MessageResponse(message="Password changed successfully")
    return GenericResponse.ok(
        data=message_response,
        status_code=200
    )

  except Exception as e:
    logger.error(f"Change password error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred while changing password",
        details=str(e),
        status_code=500
    )


@router.get("/me", response_model=GenericResponse[Dict[str, Any]])
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Get current user information from token.
  """
  try:
    auth_service = AuthService()

    user_info = await auth_service.validate_user_token(credentials.credentials)

    if not user_info:
      return GenericResponse.error(
          message="Invalid token",
          status_code=401
      )

    return GenericResponse.ok(
        data=user_info,
        status_code=200
    )

  except Exception as e:
    logger.error(f"Get current user error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred while retrieving user information",
        details=str(e),
        status_code=500
    )
