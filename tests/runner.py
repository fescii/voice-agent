"""
Main test runner for all system tests.
"""
from core.config.registry import config_registry
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize config
config_registry.initialize()


async def setup_test_database():
  """Setup test database tables."""
  print("🔧 Setting up test database...")
  try:
    # List actual tables first
    actual_tables = await debug_list_tables()

    from data.db.ops.sync.tables import DatabaseSyncService
    sync_service = DatabaseSyncService()
    result = await sync_service.sync_tables()

    # List tables again after sync
    actual_tables_after = await debug_list_tables()

    print(
        f"✅ Database tables synced successfully: {result.get('tables_created', 0)} created, {result.get('tables_skipped', 0)} skipped\n")
  except Exception as e:
    print(f"❌ Failed to sync database tables: {e}\n")
    raise


async def debug_list_tables():
  """Debug function to list actual tables in database."""
  try:
    from data.db.connection import get_async_engine
    from sqlalchemy import text

    async with get_async_engine().begin() as conn:
      result = await conn.execute(text(
          "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"
      ))
      tables = [row[0] for row in result.fetchall()]
      print(f"🔍 Actual tables in database: {tables}")
      return tables
  except Exception as e:
    print(f"❌ Error listing tables: {e}")
    return []


async def run_all_tests():
  """Run all tests in the system."""
  print("🧪 Starting comprehensive system tests...\n")

  # Setup database first
  await setup_test_database()

  # Database user operations tests
  print("=" * 50)
  print("DATABASE USER OPERATIONS TESTS")
  print("=" * 50)

  try:
    from tests.data.db.ops.user.create import run_tests as run_user_create_tests
    await run_user_create_tests()
    print()
  except Exception as e:
    print(f"❌ User create tests failed to run: {e}\n")

  try:
    from tests.data.db.ops.user.read import run_tests as run_user_read_tests
    await run_user_read_tests()
    print()
  except Exception as e:
    print(f"❌ User read tests failed to run: {e}\n")

  # Security/Authentication tests
  print("=" * 50)
  print("SECURITY & AUTHENTICATION TESTS")
  print("=" * 50)

  try:
    from tests.core.security.auth.password import run_tests as run_password_tests
    await run_password_tests()
    print()
  except Exception as e:
    print(f"❌ Password tests failed to run: {e}\n")

  try:
    from tests.core.security.auth.jwt import run_tests as run_jwt_tests
    await run_jwt_tests()
    print()
  except Exception as e:
    print(f"❌ JWT tests failed to run: {e}\n")

  # CRM model tests
  print("=" * 50)
  print("CRM MODEL TESTS")
  print("=" * 50)

  try:
    from tests.data.db.models.contact import run_tests as run_contact_tests
    await run_contact_tests()
    print()
  except Exception as e:
    print(f"❌ Contact model tests failed to run: {e}\n")

  print("=" * 50)
  print("🎉 Test run completed!")
  print("=" * 50)


if __name__ == "__main__":
  asyncio.run(run_all_tests())
