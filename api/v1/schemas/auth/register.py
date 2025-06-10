"""
User registration and profile schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from data.db.models.user import UserRole


class RegisterRequest(BaseModel):
  """User registration request schema."""
  email: EmailStr = Field(..., description="User email address")
  password: str = Field(..., min_length=8, description="User password")
  full_name: str = Field(..., min_length=2, max_length=255,
                         description="User full name")
  first_name: Optional[str] = Field(
      None, max_length=255, description="First name")
  last_name: Optional[str] = Field(
      None, max_length=255, description="Last name")
  phone: Optional[str] = Field(None, max_length=50, description="Phone number")
  role: Optional[UserRole] = Field(
      default=UserRole.USER, description="User role")


class RegisterResponse(BaseModel):
  """User registration response schema."""
  user: "UserProfile" = Field(..., description="Created user information")
  message: str = Field(default="User registered successfully",
                       description="Success message")


class UserProfile(BaseModel):
  """User profile schema."""
  id: str = Field(..., description="User ID")
  email: str = Field(..., description="User email")
  full_name: str = Field(..., description="User full name")
  first_name: Optional[str] = Field(None, description="First name")
  last_name: Optional[str] = Field(None, description="Last name")
  phone: Optional[str] = Field(None, description="Phone number")
  role: str = Field(..., description="User role")
  is_active: bool = Field(..., description="User active status")
  is_verified: bool = Field(..., description="Email verification status")
  created_at: str = Field(..., description="Account creation timestamp")
  last_login: Optional[str] = Field(None, description="Last login timestamp")


class UpdateProfileRequest(BaseModel):
  """Update user profile request schema."""
  full_name: Optional[str] = Field(
      None, min_length=2, max_length=255, description="User full name")
  first_name: Optional[str] = Field(
      None, max_length=255, description="First name")
  last_name: Optional[str] = Field(
      None, max_length=255, description="Last name")
  phone: Optional[str] = Field(None, max_length=50, description="Phone number")


# Update forward references
RegisterResponse.model_rebuild()
