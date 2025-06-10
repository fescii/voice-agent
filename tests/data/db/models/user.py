"""
User model tests.
"""
import pytest
from data.db.models.user import User, UserRole


class TestUserModel:
  """Test User model functionality."""

  def test_user_model_exists(self):
    """Test that User model can be imported and instantiated."""
    user = User()
    assert user is not None
    assert hasattr(user, 'email')
    assert hasattr(user, 'username')
    assert hasattr(user, 'password_hash')
    assert hasattr(user, 'role')

  def test_user_roles_enum(self):
    """Test user role enumeration values."""
    assert UserRole.USER.value == "user"
    assert UserRole.AGENT.value == "agent"
    assert UserRole.ADMIN.value == "admin"
    assert UserRole.SUPER_ADMIN.value == "super_admin"

  def test_password_methods_exist(self):
    """Test that password methods exist on user model."""
    user = User()
    assert hasattr(user, 'set_password')
    assert hasattr(user, 'verify_password')
    assert callable(user.set_password)
    assert callable(user.verify_password)

  def test_tablename(self):
    """Test that table name is set correctly."""
    assert User.__tablename__ == "users"
