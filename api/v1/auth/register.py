"""
User registration and profile management API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime

from api.v1.schemas.auth.register import (
    RegisterRequest, RegisterResponse, UserProfile, UpdateProfileRequest
)
from api.v1.schemas.auth.login import MessageResponse
from data.db.connection import get_db_session
from data.db.ops.user.create import create_user
from data.db.ops.user.read import get_user_by_email, get_user_by_id
from data.db.ops.user.update import update_user_profile
from core.security.auth.service import AuthService
from core.logging.setup import get_logger

router = APIRouter(prefix="/auth", tags=["authentication", "user-management"])
security = HTTPBearer()
logger = get_logger(__name__)


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
  """
  Register a new user account.
  """
  async with get_db_session() as session:
    # Check if user already exists
    existing_user = await get_user_by_email(session, request.email)
    if existing_user:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="User with this email already exists"
      )

    # Create new user
    user_data = {
        "email": request.email,
        "full_name": request.full_name,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "phone": request.phone,
        "role": request.role or "user"
    }

    user = await create_user(session, password=request.password, **user_data)

    if not user:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Failed to create user account"
      )

    # Convert user to profile schema
    user_profile = UserProfile(
        id=str(user.id),
        email=str(user.email),
        full_name=str(user.full_name or ""),
        first_name=str(
            user.first_name) if user.first_name is not None else None,
        last_name=str(user.last_name) if user.last_name is not None else None,
        phone=str(user.phone) if user.phone is not None else None,
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login is not None else None
    )

    return RegisterResponse(user=user_profile)


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Get current user profile.
  """
  auth_service = AuthService()

  # Validate token and get user info
  user_info = await auth_service.validate_user_token(credentials.credentials)

  if not user_info:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

  # Get full user details from database
  async with get_db_session() as session:
    user = await get_user_by_id(session, user_info["user_id"])

    if not user:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="User not found"
      )

    return UserProfile(
        id=str(user.id),
        email=str(user.email),
        full_name=str(user.full_name or ""),
        first_name=str(
            user.first_name) if user.first_name is not None else None,
        last_name=str(user.last_name) if user.last_name is not None else None,
        phone=str(user.phone) if user.phone is not None else None,
        role=user.role.value,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat(),
        last_login=user.last_login.isoformat() if user.last_login is not None else None
    )


@router.put("/profile", response_model=MessageResponse)
async def update_profile(
    request: UpdateProfileRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
  """
  Update current user profile.
  """
  auth_service = AuthService()

  # Validate token and get user info
  user_info = await auth_service.validate_user_token(credentials.credentials)

  if not user_info:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
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
    update_data["phone"] = request.phone

  if not update_data:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No fields to update"
    )

  async with get_db_session() as session:
    success = await update_user_profile(session, user_info["user_id"], **update_data)

    if not success:
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Failed to update profile"
      )

  return MessageResponse(message="Profile updated successfully")
