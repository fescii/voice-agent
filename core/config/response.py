"""
Generic API response classes for consistent API responses across all endpoints.
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional, TypeVar, Generic


class HealthCheckResponse(BaseModel):
  """Model for health check response."""
  status: str  # 'ok' or 'error'
  # Detailed information about system resources and dependencies
  details: Dict[str, Any]


# Define a generic response model
T = TypeVar('T')


class GenericResponse(BaseModel, Generic[T]):
  """
  Generic API response - simple and clean.
  Takes any data object, has .ok() and .error() class methods.
  """
  success: bool = True
  data: Optional[T] = None
  error_message: Optional[str] = None
  error_details: Optional[Any] = None
  status_code: Optional[int] = None

  @classmethod
  def error(cls, message: str, details: Optional[Any] = None, status_code: int = 500):
    """Create an error response."""
    return cls(success=False, data=None, error_message=message, error_details=details, status_code=status_code)

  @classmethod
  def ok(cls, data: Optional[Any] = None, status_code: int = 200):
    """Create a success response."""
    return cls(success=True, data=data, status_code=status_code)


class MessageResponse(BaseModel):
  """Simple message response model."""
  message: str
