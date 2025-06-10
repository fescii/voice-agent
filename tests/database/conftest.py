"""
Test configuration for database tests.
"""
import os
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.config.registry import config_registry
from data.db.base import Base

# Test database configuration
TEST_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/voice_agents_test"


@pytest.fixture(scope="session")
def event_loop():
  """Create an instance of the default event loop for the test session."""
  loop = asyncio.get_event_loop_policy().new_event_loop()
  yield loop
  loop.close()


@pytest.fixture(scope="session")
async def test_engine():
  """Create test database engine."""
  # Override database URL for testing
  os.environ["DB_DATABASE"] = "voice_agents_test"

  # Initialize config
  config_registry.initialize()

  # Create test engine
  engine = create_async_engine(
      TEST_DB_URL,
      echo=False,
      pool_pre_ping=True
  )

  # Create all tables
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  yield engine

  # Clean up
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)

  await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
  """Create test database session."""
  from sqlalchemy.ext.asyncio import async_sessionmaker

  async_session = async_sessionmaker(
      test_engine, class_=AsyncSession, expire_on_commit=False
  )

  async with async_session() as session:
    yield session
