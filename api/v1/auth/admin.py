"""
Admin user management API endpoints.
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from api.v1.schemas.auth.register import UserProfile
from api.v1.schemas.auth.login import MessageResponse
from data.db.connection import get_db_session
from data.db.ops.user.read import get_all_users, get_user_by_id
from data.db.ops.user.update import update_user_status
from data.db.models.user import UserRole
from core.security.auth.service import AuthService
from core.logging.setup import get_logger

router = APIRouter(prefix="/auth/admin", tags=["authentication", "admin"])
security = HTTPBearer()
logger = get_logger(__name__)


async def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
  """Dependency to require admin role."""
  auth_service = AuthService()

  user_info = await auth_service.validate_user_token(credentials.credentials)

  if not user_info:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token"
    )

  if user_info["role"] not in ["admin", "super_admin"]:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Admin access required"
    )

  return user_info


@router.get("/users", response_model=List[UserProfile])
async def list_users(
    admin_user: dict = Depends(require_admin),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    role: Optional[str] = Query(default=None),
    active_only: bool = Query(default=False)
):
  """
  List all users (admin only).
  """
  async with get_db_session() as session:
    users = await get_all_users(
        session,
        limit=limit,
        offset=offset,
        role=role,
        active_only=active_only
    )

    user_profiles = []
    for user in users:
      user_profiles.append(UserProfile(
          id=str(user.id),
          email=str(user.email),
          full_name=str(user.full_name or ""),
          first_name=str(
              user.first_name) if user.first_name is not None else None,
          last_name=str(
              user.last_name) if user.last_name is not None else None,
          phone=str(user.phone) if user.phone is not None else None,
          role=user.role.value,
          is_active=user.is_active,
          is_verified=user.is_verified,
          created_at=user.created_at.isoformat(),
          last_login=user.last_login.isoformat() if user.last_login is not None else None
      ))

    return user_profiles


@router.get("/users/{user_id}", response_model=UserProfile)
async def get_user(
    user_id: str,
    admin_user: dict = Depends(require_admin)
):
  """
  Get specific user by ID (admin only).
  """
  async with get_db_session() as session:
    try:
      user = await get_user_by_id(session, int(user_id))
    except ValueError:
      raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Invalid user ID format"
      )

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


@router.put("/users/{user_id}/activate", response_model=MessageResponse)
async def activate_user(
    user_id: str,
    admin_user: dict = Depends(require_admin)
):
  """
  Activate user account (admin only).
  """
  async with get_db_session() as session:
    success = await update_user_status(session, user_id, is_active=True)

    if not success:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="User not found or update failed"
      )

  return MessageResponse(message="User activated successfully")


@router.put("/users/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user(
    user_id: str,
    admin_user: dict = Depends(require_admin)
):
  """
  Deactivate user account (admin only).
  """
  async with get_db_session() as session:
    success = await update_user_status(session, user_id, is_active=False)

    if not success:
      raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="User not found or update failed"
      )

  return MessageResponse(message="User deactivated successfully")
