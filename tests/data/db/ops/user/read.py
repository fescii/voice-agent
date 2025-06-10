"""
User read operations tests.
"""
import asyncio
from data.db.connection import get_db_session
from data.db.ops.user.create import create_user
from data.db.ops.user.read import get_user_by_email, get_user_by_id
from data.db.models.user import UserRole


class UserReadTests:
  """Tests for user read operations."""

  async def read_user_by_email(self):
    """Test reading user by email."""
    async with get_db_session() as session:
      # Create a test user first
      user = await create_user(
          session=session,
          username="testuser",
          email="readtest@example.com",
          password="testpassword123",
          first_name="Read",
          last_name="Test"
      )

      assert user is not None

      # Now try to read it by email
      found_user = await get_user_by_email(session, "readtest@example.com")

      assert found_user is not None
      assert str(found_user.email) == "readtest@example.com"
      assert str(found_user.id) == str(user.id)

      # Clean up
      await session.delete(user)
      await session.commit()

  async def read_user_by_id(self):
    """Test reading user by ID."""
    async with get_db_session() as session:
      # Try to find existing user first, or create a new one
      existing_user = await get_user_by_email(session, "idtest@example.com")
      if existing_user:
        user = existing_user
        user_id = getattr(existing_user, 'id', 0)  # Safely get the actual ID value
        should_cleanup = False
      else:
        # Create a test user first
        user = await create_user(
            session=session,
            username="idtestuser",
            email="idtest@example.com",
            password="testpassword123",
            first_name="ID",
            last_name="Test"
        )
        assert user is not None
        await session.flush()  # Ensure the user has an ID
        user_id = getattr(user, 'id', 0)  # Safely get the actual ID value
        should_cleanup = True

      assert user is not None

      # Now try to read it by ID
      found_user = await get_user_by_id(session, user_id)

      assert found_user is not None
      assert getattr(found_user, 'id', None) == user_id  # Compare actual values safely
      assert str(found_user.email) == "idtest@example.com"

      # Clean up only if we created the user
      if should_cleanup:
        await session.delete(user)
        await session.commit()


async def run_tests():
  """Run all user read tests."""
  test_instance = UserReadTests()

  print("Running user read tests...")

  try:
    await test_instance.read_user_by_email()
    print("✅ read_user_by_email passed")
  except Exception as e:
    print(f"❌ read_user_by_email failed: {e}")

  try:
    await test_instance.read_user_by_id()
    print("✅ read_user_by_id passed")
  except Exception as e:
    print(f"❌ read_user_by_id failed: {e}")


if __name__ == "__main__":
  asyncio.run(run_tests())
