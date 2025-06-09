# Using PostgreSQL with the Startup Service

This document provides information on how to use the PostgreSQL database service
with the application startup context.

## PostgreSQL Setup for Voice Agent System

The voice agent system uses PostgreSQL as its primary database, managed through SQLAlchemy
with asyncpg as the async driver.

### Configuration

Database connection settings are managed in `core/config/providers/database.py`. The system
reads these settings from environment variables:

- `DB_HOST`: PostgreSQL host (default: localhost)
- `DB_PORT`: PostgreSQL port (default: 5432)
- `DB_USERNAME`: Database username (default: postgres)
- `DB_PASSWORD`: Database password (required)
- `DB_DATABASE`: Database name (default: voice_agents)
- `DB_POOL_SIZE`: Connection pool size (default: 10)
- `DB_MAX_OVERFLOW`: Max overflow connections (default: 20)

### Database Initialization

The database service is automatically initialized during application startup through
the startup context system. This creates the connection pool and verifies connectivity.

### Using the Database in API Endpoints

You can access the database service through the startup context:

```python
from fastapi import APIRouter, Depends
from core.startup.context import get_startup_context

router = APIRouter()

@router.get("/database-status")
async def get_database_status(context = Depends(get_startup_context)):
    # Check if database service is healthy
    db_status = context.get_service_status("database")
    
    if db_status and db_status.status == "running":
        # Database is healthy
        return {
            "status": "healthy",
            "database": db_status.metadata.get("database")
        }
    else:
        return {"status": "unhealthy"}
```

### Admin API

A dedicated admin API is available at `/api/v1/admin/database` that provides:

- Overall database health
- Connection statistics
- Table information
- Schema details

### Accessing PostgreSQL Status

For more detailed PostgreSQL statistics, you can use the database service directly:

```python
from core.startup.services.database import DatabaseService

async def get_tables_info():
    db_service = DatabaseService()
    tables_info = await db_service.check_postgres_tables()
    return tables_info
```
