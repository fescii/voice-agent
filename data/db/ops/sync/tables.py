"""
Database table synchronization service.
Handles table creation if they don't exist, skips if they do.
"""
from typing import Dict, Any, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, inspect

from data.db.connection import get_async_engine
from data.db.base import Base
from data.db.models import (
    CallLog, AgentConfig, Transcript, User, AgentMemory,
    Contact, Company, Deal, Activity, Task
)
from core.logging.setup import get_logger

logger = get_logger(__name__)


class DatabaseSyncService:
  """Service for synchronizing database tables on startup."""

  def __init__(self):
    # Order models by dependencies (base tables first, then dependent tables)
    self.models = [
        # Base tables with no dependencies
        User,
        AgentConfig,
        AgentMemory,
        # CRM tables that may depend on User
        Contact,
        Company,
        Deal,
        Activity,
        Task,
        # Call-related tables
        CallLog,
        Transcript  # Depends on CallLog
    ]

  async def sync_tables(self) -> Dict[str, Any]:
    """
    Sync all database tables.
    Creates tables if they don't exist, skips if they do.

    Returns:
        Dict containing sync results and statistics
    """
    logger.info("Starting database table synchronization...")

    # Import all models to ensure they're registered with Base.metadata
    from data.db.models import (
        CallLog, AgentConfig, Transcript, User, AgentMemory,
        Contact, Company, Deal, Activity, Task
    )

    print(f"📊 Metadata tables registered: {list(Base.metadata.tables.keys())}")

    results = {
        "tables_checked": 0,
        "tables_created": 0,
        "tables_skipped": 0,
        "errors": [],
        "created_tables": [],
        "existing_tables": []
    }

    try:
      # Get existing tables first
      async with get_async_engine().begin() as conn:
        existing_tables = await self._get_existing_tables(conn)

      # Check each model's table
      tables_to_create = []
      for model in self.models:
        table_name = model.__tablename__
        results["tables_checked"] += 1

        if table_name in existing_tables:
          logger.info(f"Table '{table_name}' already exists, skipping...")
          results["tables_skipped"] += 1
          results["existing_tables"].append(table_name)
        else:
          tables_to_create.append(table_name)

      # Create all missing tables at once using metadata
      if tables_to_create:
        logger.info(
            f"Creating {len(tables_to_create)} tables: {', '.join(tables_to_create)}")
        try:
          async with get_async_engine().begin() as conn:
            # Create all tables from metadata - handles dependencies automatically
            await conn.run_sync(Base.metadata.create_all, checkfirst=True)

          results["tables_created"] = len(tables_to_create)
          results["created_tables"] = tables_to_create
          logger.info(f"✅ Created {len(tables_to_create)} tables successfully")
        except Exception as e:
          error_msg = f"Failed to create tables: {str(e)}"
          logger.error(error_msg)
          results["errors"].append(error_msg)

      # Log summary
      logger.info(f"Database sync completed:")
      logger.info(f"  - Tables checked: {results['tables_checked']}")
      logger.info(f"  - Tables created: {results['tables_created']}")
      logger.info(f"  - Tables skipped: {results['tables_skipped']}")
      logger.info(f"  - Errors: {len(results['errors'])}")

      if results["created_tables"]:
        logger.info(f"  - Created: {', '.join(results['created_tables'])}")

      if results["errors"]:
        logger.warning(f"  - Errors occurred: {'; '.join(results['errors'])}")

      return results

    except SQLAlchemyError as e:
      error_msg = f"Database sync failed: {str(e)}"
      logger.error(error_msg)
      results["errors"].append(error_msg)
      return results
    except Exception as e:
      error_msg = f"Unexpected error during database sync: {str(e)}"
      logger.error(error_msg)
      results["errors"].append(error_msg)
      return results

  async def _get_existing_tables(self, conn) -> List[str]:
    """Get list of existing tables in the database."""
    try:
      # Query to get all table names in the public schema
      query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
      """)

      result = await conn.execute(query)
      tables = [row[0] for row in result]
      logger.info(f"Found {len(tables)} existing tables: {', '.join(tables)}")
      return tables

    except Exception as e:
      logger.error(f"Error getting existing tables: {str(e)}")
      return []

  async def create_all_tables(self) -> Dict[str, Any]:
    """
    Create all tables (destructive operation - use with caution).
    This will create all tables regardless of whether they exist.
    """
    logger.warning("Creating ALL tables - this may overwrite existing data!")

    try:
      async with get_async_engine().begin() as conn:
        # Create all tables from metadata
        await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ All tables created successfully")
        return {
            "status": "success",
            "message": "All tables created",
            "tables": [model.__tablename__ for model in self.models]
        }

    except Exception as e:
      error_msg = f"Failed to create all tables: {str(e)}"
      logger.error(error_msg)
      return {
          "status": "error",
          "message": error_msg,
          "tables": []
      }

  async def drop_all_tables(self) -> Dict[str, Any]:
    """
    Drop all tables (destructive operation - use with extreme caution).
    """
    logger.warning("Dropping ALL tables - this will DELETE all data!")

    try:
      async with get_async_engine().begin() as conn:
        # Drop all tables from metadata
        await conn.run_sync(Base.metadata.drop_all)

        logger.info("✅ All tables dropped successfully")
        return {
            "status": "success",
            "message": "All tables dropped",
            "tables": [model.__tablename__ for model in self.models]
        }

    except Exception as e:
      error_msg = f"Failed to drop all tables: {str(e)}"
      logger.error(error_msg)
      return {
          "status": "error",
          "message": error_msg,
          "tables": []
      }
