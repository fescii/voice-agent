"""
User registration and profile management API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from sqlalchemy import select

from api.v1.schemas.auth.register import (
    RegisterRequest, RegisterResponse, UserProfile, UpdateProfileRequest
)
from core.config.response import GenericResponse, MessageResponse
from data.db.connection import get_db_session
from data.db.models.user import User, UserRole, UserStatus
from data.db.ops.user.create import create_user
from data.db.ops.user.read import get_user_by_email, get_user_by_id
from data.db.ops.user.update import update_user_profile
from core.security.auth.service import AuthService
from core.logging.setup import get_logger

router = APIRouter(prefix="/auth", tags=["authentication", "user-management"])
security = HTTPBearer()
logger = get_logger(__name__)


@router.post("/register", response_model=GenericResponse[RegisterResponse])
async def register(request: RegisterRequest):
  """
  Register a new user account.
  """
  try:
    async with get_db_session() as session:
      # Check if user already exists
      existing_user = await get_user_by_email(session, request.email)
      if existing_user:
        return GenericResponse.error(
            message="User with this email already exists",
            status_code=400
        )

      # Generate username from email (before @ symbol)
      username = request.email.split('@')[0]

      # Ensure username is unique by appending numbers if needed
      base_username = username
      counter = 1
      while True:
        existing_username = await session.execute(
            select(User).where(User.username == username)
        )
        if not existing_username.scalar_one_or_none():
          break
        username = f"{base_username}{counter}"
        counter += 1

      # Create new user
      user = await create_user(
          session=session,
          username=username,
          email=request.email,
          password=request.password,
          first_name=request.first_name or "",
          last_name=request.last_name or "",
          phone_primary=request.phone,  # Use phone_primary instead of phone
          role=request.role or UserRole.USER
      )

      if not user:
        return GenericResponse.error(
            message="Failed to create user account",
            details="An error occurred while creating the user account",
            status_code=500
        )

      # Convert user to profile schema
      user_profile = UserProfile(
          id=str(user.id),
          email=str(user.email),
          full_name=str(user.full_name or ""),
          first_name=str(
              user.first_name) if user.first_name is not None else None,
          last_name=str(
              user.last_name) if user.last_name is not None else None,
          phone=str(
              user.phone_primary) if user.phone_primary is not None else None,
          role=user.role.value if user.role is not None else "user",
          is_active=user.status.value == "active" if user.status is not None else False,
          is_verified=bool(
              user.email_verified) if user.email_verified is not None else False,
          created_at=user.created_at.isoformat() if user.created_at is not None else "",
          last_login=user.last_login.isoformat() if user.last_login is not None else None
      )

      response_data = RegisterResponse(
          user=user_profile,
          message="User registered successfully"
      )

      return GenericResponse(
          success=True,
          data=response_data
      )

  except Exception as e:
    logger.error(f"Registration error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred during registration",
        details=str(e),
        status_code=500
    )


@router.get("/profile", response_model=GenericResponse[UserProfile])
async def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Get current user profile.
  """
  try:
    auth_service = AuthService()

    # Validate token and get user info
    user_info = await auth_service.validate_user_token(credentials.credentials)

    if not user_info:
      return GenericResponse.error(
          message="Invalid or expired token",
          status_code=401
      )

    # Get full user details from database
    async with get_db_session() as session:
      user = await get_user_by_id(session, user_info["user_id"])

      if not user:
        return GenericResponse.error(
            message="User not found",
            status_code=404
        )

      user_profile = UserProfile(
          id=str(user.id),
          email=str(user.email),
          full_name=str(user.full_name or ""),
          first_name=str(
              user.first_name) if user.first_name is not None else None,
          last_name=str(
              user.last_name) if user.last_name is not None else None,
          phone=str(
              user.phone_primary) if user.phone_primary is not None else None,
          role=user.role.value if user.role is not None else "user",
          is_active=user.status.value == "active" if user.status is not None else False,
          is_verified=bool(
              user.email_verified) if user.email_verified is not None else False,
          created_at=user.created_at.isoformat() if user.created_at is not None else "",
          last_login=user.last_login.isoformat() if user.last_login is not None else None
      )

      return GenericResponse(
          success=True,
          data=user_profile
      )

  except Exception as e:
    logger.error(f"Profile retrieval error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred while retrieving user profile",
        details=str(e),
        status_code=500
    )


@router.put("/profile", response_model=GenericResponse[MessageResponse])
async def update_profile(
    request: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Update current user profile.
  """
  try:
    auth_service = AuthService()

    # Validate token and get user info
    user_info = await auth_service.validate_user_token(credentials.credentials)

    if not user_info:
      return GenericResponse.error(
          message="Invalid or expired token",
          status_code=401
      )

    # Update user profile
    update_data = {}
    if request.full_name is not None:
      update_data["full_name"] = request.full_name
    if request.first_name is not None:
      update_data["first_name"] = request.first_name
    if request.last_name is not None:
      update_data["last_name"] = request.last_name
    if request.phone is not None:
      update_data["phone_primary"] = request.phone  # Use phone_primary

    if not update_data:
      return GenericResponse.error(
          message="No fields to update",
          status_code=400
      )

    async with get_db_session() as session:
      success = await update_user_profile(session, user_info["user_id"], **update_data)

      if not success:
        return GenericResponse.error(
            message="Failed to update profile",
            status_code=500
        )

    message_response = MessageResponse(message="Profile updated successfully")

    return GenericResponse(
        success=True,
        data=message_response
    )

  except Exception as e:
    logger.error(f"Profile update error: {str(e)}")
    return GenericResponse.error(
        message="An error occurred while updating user profile",
        details=str(e),
        status_code=500
    )
