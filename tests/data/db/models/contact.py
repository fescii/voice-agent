"""
Contact model basic tests.
"""
import asyncio
from data.db.connection import get_db_session
from data.db.models.contact import Contact


class ContactModelTests:
  """Tests for contact model."""

  async def create_basic_contact(self):
    """Test creating a basic contact."""
    async with get_db_session() as session:
      contact = Contact(
          phone_primary="+1234567890",
          first_name="John",
          last_name="Doe",
          email_primary="john.doe@example.com"
      )

      session.add(contact)
      await session.commit()
      await session.refresh(contact)

      assert contact.id is not None
      assert str(contact.first_name) == "John"
      assert str(contact.last_name) == "Doe"
      assert str(contact.email_primary) == "john.doe@example.com"
      assert str(contact.phone_primary) == "+1234567890"

      # Clean up
      await session.delete(contact)
      await session.commit()


async def run_tests():
  """Run all contact model tests."""
  test_instance = ContactModelTests()

  print("Running contact model tests...")

  try:
    await test_instance.create_basic_contact()
    print("✅ create_basic_contact passed")
  except Exception as e:
    print(f"❌ create_basic_contact failed: {e}")


if __name__ == "__main__":
  asyncio.run(run_tests())
