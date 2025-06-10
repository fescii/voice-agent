"""
Test configuration and shared fixtures.
"""
import pytest
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from core.config.registry import config_registry
from data.db.base import Base


@pytest.fixture(scope="session")
def event_loop():
  """Create an instance of the default event loop for the test session."""
  loop = asyncio.get_event_loop_policy().new_event_loop()
  yield loop
  loop.close()


@pytest.fixture(scope="session")
async def test_engine():
  """Create a test database engine."""
  # Initialize config
  config_registry.initialize()

  # Use test database URL
  test_db_url = os.getenv(
      "TEST_DATABASE_URL",
      "postgresql+asyncpg://postgres:postgres@localhost:5432/voice_agents_test"
  )

  engine = create_async_engine(
      test_db_url,
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
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
  """Create a test database session."""
  from sqlalchemy.ext.asyncio import async_sessionmaker

  async_session = async_sessionmaker(
      test_engine, class_=AsyncSession, expire_on_commit=False
  )

  async with async_session() as session:
    try:
      yield session
      await session.commit()
    except Exception:
      await session.rollback()
      raise
    finally:
      await session.close()


@pytest.fixture
def test_user_data():
  """Sample user data for testing."""
  return {
      "email": "test@example.com",
      "username": "testuser",
      "first_name": "Test",
      "last_name": "User",
      "full_name": "Test User",
      "password": "testpassword123"
  }


@pytest.fixture
def test_contact_data():
  """Sample contact data for testing."""
  return {
      "phone_primary": "+1234567890",
      "email_primary": "contact@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "full_name": "John Doe"
  }


@pytest.fixture
def test_company_data():
  """Sample company data for testing."""
  return {
      "name": "Test Company Inc.",
      "domain": "testcompany.com",
      "industry": "Technology"
  }
