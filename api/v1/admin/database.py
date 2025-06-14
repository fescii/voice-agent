"""
Database administration API endpoints.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from core.startup.context import get_startup_context
from core.startup.services.database import DatabaseService
from core.config.response import GenericResponse

router = APIRouter(prefix="/database", tags=["admin", "database"])


@router.get("/stats", response_model=GenericResponse[Dict[str, Any]])
async def get_database_stats(context=Depends(get_startup_context)):
  """
  Get database statistics and health information.

  Requires admin access.
  """
  try:
    service_status = context.get_service_status("database")

    if not service_status or service_status.status != "running":
      return GenericResponse.error("Database service is not available", status.HTTP_503_SERVICE_UNAVAILABLE)

    # Get the database service instance
    db_service = DatabaseService()

    # Get detailed database statistics
    stats = await db_service.get_database_stats()

    # Get table information
    tables = await db_service.check_postgres_tables()

    data = {
        "status": stats["status"],
        "connections": stats.get("connections", 0),
        "database": stats.get("database", "unknown"),
        "tables": tables.get("total_tables", 0),
        "schemas": tables.get("total_schemas", 0),
        "tables_by_schema": tables.get("tables_by_schema", {})
    }

    return GenericResponse.ok(data)
  except Exception as e:
    return GenericResponse.error(f"Failed to get database stats: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
