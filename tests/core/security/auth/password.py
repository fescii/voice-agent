"""
Password service tests.
"""
import asyncio
from core.security.auth.password import PasswordService


class PasswordServiceTests:
  """Tests for password hashing and verification."""

  def __init__(self):
    self.password_service = PasswordService()

  async def hash_password(self):
    """Test password hashing."""
    password = "testpassword123"
    hashed = self.password_service.hash_password(password)

    assert hashed is not None
    assert len(hashed) > 20  # bcrypt hashes are long
    assert hashed != password  # Should be different
    assert hashed.startswith("$2b$")  # bcrypt format

  async def verify_password_correct(self):
    """Test password verification with correct password."""
    password = "testpassword123"
    hashed = self.password_service.hash_password(password)

    is_valid = self.password_service.verify_password(password, hashed)
    assert is_valid == True

  async def verify_password_incorrect(self):
    """Test password verification with incorrect password."""
    password = "testpassword123"
    wrong_password = "wrongpassword456"
    hashed = self.password_service.hash_password(password)

    is_valid = self.password_service.verify_password(wrong_password, hashed)
    assert is_valid == False

  async def generate_temp_password(self):
    """Test temporary password generation."""
    temp_password = self.password_service.generate_temp_password(12)

    assert temp_password is not None
    assert len(temp_password) == 12
    assert isinstance(temp_password, str)

    # Generate another and ensure they're different
    temp_password2 = self.password_service.generate_temp_password(12)
    assert temp_password != temp_password2


async def run_tests():
  """Run all password service tests."""
  test_instance = PasswordServiceTests()

  print("Running password service tests...")

  try:
    await test_instance.hash_password()
    print("✅ hash_password passed")
  except Exception as e:
    print(f"❌ hash_password failed: {e}")

  try:
    await test_instance.verify_password_correct()
    print("✅ verify_password_correct passed")
  except Exception as e:
    print(f"❌ verify_password_correct failed: {e}")

  try:
    await test_instance.verify_password_incorrect()
    print("✅ verify_password_incorrect passed")
  except Exception as e:
    print(f"❌ verify_password_incorrect failed: {e}")

  try:
    await test_instance.generate_temp_password()
    print("✅ generate_temp_password passed")
  except Exception as e:
    print(f"❌ generate_temp_password failed: {e}")


if __name__ == "__main__":
  asyncio.run(run_tests())
