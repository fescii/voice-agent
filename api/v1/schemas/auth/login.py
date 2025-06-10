"""
Login and logout request/response schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class LoginRequest(BaseModel):
  """Login request schema."""
  email: EmailStr = Field(..., description="User email address")
  password: str = Field(..., min_length=8, description="User password")


class LoginResponse(BaseModel):
  """Login response schema."""
  access_token: str = Field(..., description="JWT access token")
  refresh_token: str = Field(..., description="JWT refresh token")
  token_type: str = Field(default="bearer", description="Token type")
  user: "UserInfo" = Field(..., description="User information")


class UserInfo(BaseModel):
  """User information schema."""
  id: str = Field(..., description="User ID")
  email: str = Field(..., description="User email")
  full_name: str = Field(..., description="User full name")
  role: str = Field(..., description="User role")
  is_active: bool = Field(..., description="User active status")


class RefreshTokenRequest(BaseModel):
  """Refresh token request schema."""
  refresh_token: str = Field(..., description="Valid refresh token")


class RefreshTokenResponse(BaseModel):
  """Refresh token response schema."""
  access_token: str = Field(..., description="New JWT access token")
  token_type: str = Field(default="bearer", description="Token type")


class LogoutRequest(BaseModel):
  """Logout request schema."""
  refresh_token: Optional[str] = Field(
      None, description="Refresh token to invalidate")


class ChangePasswordRequest(BaseModel):
  """Change password request schema."""
  old_password: str = Field(..., min_length=8, description="Current password")
  new_password: str = Field(..., min_length=8, description="New password")


class MessageResponse(BaseModel):
  """Generic message response schema."""
  message: str = Field(..., description="Response message")
  success: bool = Field(default=True, description="Operation success status")


# Update forward references
LoginResponse.model_rebuild()
