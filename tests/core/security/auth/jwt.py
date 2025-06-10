"""
JWT token service tests.
"""
import asyncio
import time
from core.security.auth.jwt import TokenService


class JWTServiceTests:
  """Tests for JWT token operations."""

  def __init__(self):
    self.token_service = TokenService()

  async def create_access_token(self):
    """Test access token creation."""
    token = self.token_service.create_access_token(
        user_id="test123",
        email="test@example.com",
        role="user"
    )

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50  # JWT tokens are long
    assert token.count('.') == 2  # JWT has 3 parts separated by dots

  async def create_refresh_token(self):
    """Test refresh token creation."""
    token = self.token_service.create_refresh_token(
        user_id="test123",
        email="test@example.com"
    )

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 50
    assert token.count('.') == 2

  async def validate_valid_token(self):
    """Test validation of valid token."""
    token = self.token_service.create_access_token(
        user_id="test123",
        email="test@example.com",
        role="user"
    )

    payload = self.token_service.validate_token(token)

    assert payload is not None
    assert payload["sub"] == "test123"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "user"
    assert payload["type"] == "access"

  async def validate_invalid_token(self):
    """Test validation of invalid token."""
    invalid_token = "invalid.token.here"

    payload = self.token_service.validate_token(invalid_token)

    assert payload is None

  async def extract_user_from_token(self):
    """Test extracting user info from token."""
    token = self.token_service.create_access_token(
        user_id="test123",
        email="test@example.com",
        role="admin"
    )

    user_info = self.token_service.extract_user_from_token(token)

    assert user_info is not None
    assert user_info["user_id"] == "test123"
    assert user_info["email"] == "test@example.com"
    assert user_info["role"] == "admin"


async def run_tests():
  """Run all JWT service tests."""
  test_instance = JWTServiceTests()

  print("Running JWT service tests...")

  try:
    await test_instance.create_access_token()
    print("✅ create_access_token passed")
  except Exception as e:
    print(f"❌ create_access_token failed: {e}")

  try:
    await test_instance.create_refresh_token()
    print("✅ create_refresh_token passed")
  except Exception as e:
    print(f"❌ create_refresh_token failed: {e}")

  try:
    await test_instance.validate_valid_token()
    print("✅ validate_valid_token passed")
  except Exception as e:
    print(f"❌ validate_valid_token failed: {e}")

  try:
    await test_instance.validate_invalid_token()
    print("✅ validate_invalid_token passed")
  except Exception as e:
    print(f"❌ validate_invalid_token failed: {e}")

  try:
    await test_instance.extract_user_from_token()
    print("✅ extract_user_from_token passed")
  except Exception as e:
    print(f"❌ extract_user_from_token failed: {e}")


if __name__ == "__main__":
  asyncio.run(run_tests())
