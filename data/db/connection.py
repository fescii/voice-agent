"""
Database connection setup (engine, session)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from core.config.providers.database import DatabaseConfig

# Global connection variables - initialized lazily
_async_engine = None
_sync_engine = None
_async_session_local = None


def get_async_engine():
  """Get async database engine (lazy initialization)."""
  global _async_engine
  if _async_engine is None:
    db_config = DatabaseConfig()
    _async_engine = create_async_engine(
        db_config.async_database_url,
        echo=db_config.echo_sql,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_pre_ping=True
    )
  return _async_engine


def get_sync_engine():
  """Get sync database engine (lazy initialization)."""
  global _sync_engine
  if _sync_engine is None:
    db_config = DatabaseConfig()
    _sync_engine = create_engine(
        db_config.sync_database_url,
        echo=db_config.echo_sql,
        pool_size=db_config.pool_size,
        max_overflow=db_config.max_overflow,
        pool_pre_ping=True
    )
  return _sync_engine


def get_async_session_local():
  """Get async session factory (lazy initialization)."""
  global _async_session_local
  if _async_session_local is None:
    from sqlalchemy.ext.asyncio import async_sessionmaker
    _async_session_local = async_sessionmaker(
        bind=get_async_engine(),
        class_=AsyncSession,
        expire_on_commit=False
    )
  return _async_session_local


# Session dependency for FastAPI
@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
  """
  Get async database session

  Yields:
      AsyncSession: Database session
  """
  session_factory = get_async_session_local()
  async with session_factory() as session:
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


# Note: Use get_async_engine(), get_sync_engine(), and get_async_session_local()
# functions instead of direct variable access to avoid import-time initialization
