"""
PostgreSQL database startup service implementation.
"""
from typing import Dict, Any, TYPE_CHECKING
from sqlalchemy.exc import SQLAlchemyError
import asyncpg

from core.startup.services.base import BaseStartupService
from data.db.connection import get_async_engine
from data.db.ops.sync.tables import DatabaseSyncService
from core.config.registry import config_registry
from core.logging.setup import get_logger
from .queries import (
    HEALTH_CHECK_QUERY,
    VERSION_QUERY,
    CONNECTION_COUNT_QUERY,
    SCHEMA_LIST_QUERY,
    TABLE_LIST_QUERY
)

if TYPE_CHECKING:
  from core.startup.manager import StartupContext

logger = get_logger(__name__)


class DatabaseService(BaseStartupService):
  """PostgreSQL database initialization service."""

  def __init__(self):
    super().__init__("database", is_critical=True)
    self.db_config = config_registry.database
    self.sync_service = DatabaseSyncService()

  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """Initialize PostgreSQL database connection and verify connectivity."""
    try:
      # Test database connection with SQLAlchemy
      async with get_async_engine().begin() as conn:
        # Basic connectivity test
        await conn.execute(HEALTH_CHECK_QUERY)

        try:
          # Try to get PostgreSQL version - simplified approach for SQLAlchemy 2.0
          version_result = await conn.execute(VERSION_QUERY)
          pg_version = version_result.scalar_one_or_none() or "Unknown"

          # Get simplified PostgreSQL stats that work across PostgreSQL versions
          stats_result = await conn.execute(CONNECTION_COUNT_QUERY)
          connections = stats_result.scalar_one_or_none() or 0
          db_stats = {
              "datname": self.db_config.database,
              "connections": connections
          }
        except Exception as e:
          logger.warning(f"Could not fetch detailed PostgreSQL stats: {e}")
          pg_version = "Unknown"
          db_stats = {
              "datname": self.db_config.database,
              "connections": 0
          }

        logger.info(f"PostgreSQL connection verified: {pg_version}")

        # Get SQLAlchemy pool metrics
        pool_info = {
            "engine_url": str(get_async_engine().url).replace(get_async_engine().url.password or '', '***'),
            "dialect": get_async_engine().dialect.name,
            "driver": "asyncpg",
            "pool_class": get_async_engine().pool.__class__.__name__,
            "pool_size": self.db_config.pool_size,
            "max_overflow": self.db_config.max_overflow,
        }

        # Add PostgreSQL database statistics
        try:
          pg_version_text = str(pg_version).split()[1] if isinstance(
              pg_version, str) and "PostgreSQL" in pg_version else "unknown"
        except (IndexError, AttributeError):
          pg_version_text = "unknown"

        postgres_info = {
            "pg_version": pg_version_text,
            "database": self.db_config.database,
            "host": self.db_config.host,
            "port": self.db_config.port,
            "active_connections": db_stats.get("connections", 0)
        }

        # Sync database tables (create if they don't exist)
        logger.info("Synchronizing database tables...")
        sync_results = await self.sync_service.sync_tables()

        # Add sync results to return metadata
        table_sync_info = {
            "tables_checked": sync_results.get("tables_checked", 0),
            "tables_created": sync_results.get("tables_created", 0),
            "tables_skipped": sync_results.get("tables_skipped", 0),
            "sync_errors": len(sync_results.get("errors", [])),
            "created_tables": sync_results.get("created_tables", []),
        }

        return {**pool_info, **postgres_info, **table_sync_info}
    except SQLAlchemyError as e:
      logger.error(f"Database connection failed: {e}")
      raise
    except Exception as e:
      logger.error(f"Unexpected database error: {e}")
      raise

  async def cleanup(self, context: "StartupContext") -> None:
    """Close PostgreSQL database connections."""
    try:
      logger.info("Closing PostgreSQL database connections...")
      await get_async_engine().dispose()
      logger.info("All PostgreSQL database connections closed successfully")
    except Exception as e:
      logger.error(f"Error closing PostgreSQL database connections: {e}")

  def get_health_check(self) -> Dict[str, Any]:
    """Get PostgreSQL database health information."""
    try:
      # For health check we can't use async in a sync method, so we just return status
      # based on initialization success
      return {
          "service": self.name,
          "status": "healthy",
          "critical": self.is_critical,
          "dialect": get_async_engine().dialect.name,
          "database": self.db_config.database,
          "host": self.db_config.host
      }
    except Exception as e:
      return {
          "service": self.name,
          "status": "unhealthy",
          "critical": self.is_critical,
          "error": str(e)
      }

  async def get_database_stats(self) -> Dict[str, Any]:
    """Get detailed PostgreSQL database statistics."""
    try:
      async with get_async_engine().connect() as conn:
        # Basic connectivity test
        result = await conn.execute(HEALTH_CHECK_QUERY)
        is_connected = result.scalar_one() == 1

        # Get connection count
        result = await conn.execute(CONNECTION_COUNT_QUERY)
        conn_count = result.scalar_one_or_none() or 0

        return {
            "status": "healthy" if is_connected else "unhealthy",
            "connections": conn_count,
            "engine": str(get_async_engine().url.drivername),
            "database": self.db_config.database,
            "host": self.db_config.host
        }
    except Exception as e:
      logger.error(f"Error getting database stats: {e}")
      return {
          "status": "unhealthy",
          "error": str(e)
      }

  async def check_postgres_tables(self) -> Dict[str, Any]:
    """Check PostgreSQL tables and schema information."""
    try:
      table_info = {}
      schema_info = {}

      async with get_async_engine().connect() as conn:
        # Get schema information
        schema_result = await conn.execute(SCHEMA_LIST_QUERY)
        schemas = [row[0] for row in schema_result]

        # Get table information
        table_result = await conn.execute(TABLE_LIST_QUERY)

        for row in table_result:
          schema_name = row[0]
          table_name = row[1]
          column_count = row[2]

          if schema_name not in schema_info:
            schema_info[schema_name] = []

          schema_info[schema_name].append({
              "name": table_name,
              "columns": column_count
          })

      return {
          "schemas": schemas,
          "tables_by_schema": schema_info,
          "total_schemas": len(schemas),
          "total_tables": sum(len(tables) for tables in schema_info.values())
      }

    except Exception as e:
      logger.error(f"Error checking database tables: {e}")
      return {
          "error": str(e),
          "schemas": [],
          "tables_by_schema": {},
          "total_schemas": 0,
          "total_tables": 0
      }
