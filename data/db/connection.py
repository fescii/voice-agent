"""
Database connection setup (engine, session)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from core.config.providers.database import DatabaseConfig

# Database configuration
db_config = DatabaseConfig()

# Create async engine
async_engine = create_async_engine(
    db_config.async_database_url,
    echo=db_config.echo_sql,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_pre_ping=True
)

# Create sync engine for migrations
sync_engine = create_engine(
    db_config.sync_database_url,
    echo=db_config.echo_sql,
    pool_size=db_config.pool_size,
    max_overflow=db_config.max_overflow,
    pool_pre_ping=True
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Session dependency for FastAPI
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get database session
    
    Yields:
        AsyncSession: Database session
    """
    async with get_db_session() as session:
        yield session
