"""
Context utilities for accessing application startup context.
"""
from typing import Any, Optional
from fastapi import Request, Depends, HTTPException, status


async def get_startup_context(request: Request) -> Any:
  """
  Dependency to get the application startup context.

  Args:
      request: The FastAPI request object

  Returns:
      The startup context

  Raises:
      HTTPException: If startup context is not available
  """
  if not hasattr(request.app.state, "startup_context"):
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Application startup context not available"
    )

  return request.app.state.startup_context


async def get_service(
    request: Request,
    service_name: str,
    required: bool = True
) -> Optional[Any]:
  """
  Get a specific service from the startup context.

  Args:
      request: The FastAPI request object
      service_name: Name of the service to get
      required: Whether the service is required

  Returns:
      The service metadata or None if not required and not found

  Raises:
      HTTPException: If service is required but not found
  """
  context = await get_startup_context(request)
  service = context.get_service_status(service_name)

  if service is None or service.status != "running":
    if required:
      raise HTTPException(
          status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
          detail=f"Service {service_name} is not available"
      )
    return None

  return service.metadata
