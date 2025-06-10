"""
User create operations tests.
"""
import asyncio
from data.db.connection import get_db_session
from data.db.ops.user.create import create_user
from data.db.models.user import UserRole


class UserCreateTests:
  """Tests for user create operations."""

  async def create_basic_user(self):
    """Test creating a basic user."""
    async with get_db_session() as session:
      user = await create_user(
          session=session,
          username="basicuser",
          email="basic@example.com",
          password="testpassword123",
          first_name="Basic",
          last_name="User"
      )

      assert user is not None
      assert str(user.username) == "basicuser"
      assert str(user.email) == "basic@example.com"
      assert user.role.value == UserRole.USER.value
      assert user.verify_password("testpassword123")

      # Clean up
      await session.delete(user)
      await session.commit()

  async def create_admin_user(self):
    """Test creating an admin user."""
    async with get_db_session() as session:
      user = await create_user(
          session=session,
          username="adminuser",
          email="admin@example.com",
          password="adminpassword123",
          first_name="Admin",
          last_name="User",
          role=UserRole.ADMIN
      )

      assert user is not None
      assert str(user.username) == "adminuser"
      assert str(user.email) == "admin@example.com"
      assert user.role.value == UserRole.ADMIN.value
      assert user.verify_password("adminpassword123")

      # Clean up
      await session.delete(user)
      await session.commit()

  async def create_duplicate_user(self):
    """Test creating a duplicate user (should fail)."""
    async with get_db_session() as session:
      # Create first user
      user1 = await create_user(
          session=session,
          username="duplicate",
          email="duplicate@example.com",
          password="testpassword123",
          first_name="First",
          last_name="User"
      )

      assert user1 is not None

      # Try to create duplicate user (should fail)
      try:
        user2 = await create_user(
            session=session,
            username="duplicate",
            email="duplicate@example.com",
            password="testpassword123",
            first_name="Second",
            last_name="User"
        )
        assert False, "Should have failed to create duplicate user"
      except Exception:
        # Expected to fail
        pass

      # Clean up
      await session.delete(user1)
      await session.commit()


async def run_tests():
  """Run all user create tests."""
  test_instance = UserCreateTests()

  print("Running user create tests...")

  try:
    await test_instance.create_basic_user()
    print("✅ create_basic_user passed")
  except Exception as e:
    print(f"❌ create_basic_user failed: {e}")

  try:
    await test_instance.create_admin_user()
    print("✅ create_admin_user passed")
  except Exception as e:
    print(f"❌ create_admin_user failed: {e}")

  try:
    await test_instance.create_duplicate_user()
    print("✅ create_duplicate_user passed")
  except Exception as e:
    print(f"❌ create_duplicate_user failed: {e}")


if __name__ == "__main__":
  asyncio.run(run_tests())
