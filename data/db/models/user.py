"""
System user database model for authentication and ownership.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Enum
from sqlalchemy.ext.hybrid import hybrid_property
from data.db.base import BaseModel
import enum
import hashlib
import secrets


class UserRole(enum.Enum):
  """User role enumeration."""
  SUPER_ADMIN = "super_admin"
  ADMIN = "admin"
  MANAGER = "manager"
  SALES_REP = "sales_rep"
  AGENT = "agent"
  USER = "user"
  READONLY = "readonly"


class UserStatus(enum.Enum):
  """User status enumeration."""
  ACTIVE = "active"
  INACTIVE = "inactive"
  SUSPENDED = "suspended"
  PENDING = "pending"
  LOCKED = "locked"


class User(BaseModel):
  """System user model for authentication and ownership."""
  __tablename__ = "users"

  # Authentication credentials
  username = Column(String(100), unique=True, index=True, nullable=False)
  email = Column(String(255), unique=True, index=True, nullable=False)
  password_hash = Column(String(255), nullable=False)
  salt = Column(String(100), nullable=False)

  # Personal information
  first_name = Column(String(255), nullable=False)
  last_name = Column(String(255), nullable=False)
  full_name = Column(String(511))  # Computed field

  # Role and permissions
  role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)
  status = Column(Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
  permissions = Column(JSON)  # Additional granular permissions

  # Contact information
  phone_primary = Column(String(50))
  phone_secondary = Column(String(50))

  # Profile details
  title = Column(String(255))
  department = Column(String(255))
  manager_id = Column(String(255), index=True)  # Reference to another user

  # Security and session management
  last_login = Column(DateTime)
  last_activity = Column(DateTime)
  failed_login_attempts = Column(String(3), default="0")
  password_reset_token = Column(String(255))
  password_reset_expires = Column(DateTime)
  email_verification_token = Column(String(255))
  email_verified = Column(Boolean, default=False)
  two_factor_enabled = Column(Boolean, default=False)
  two_factor_secret = Column(String(255))

  # Account settings
  timezone = Column(String(50), default="UTC")
  preferred_language = Column(String(10), default="en")
  theme = Column(String(50), default="light")

  # CRM ownership and quotas
  sales_quota = Column(String(50))  # Monthly/yearly quota
  commission_rate = Column(String(10))  # Percentage as string
  territory = Column(String(255))

  # System metadata
  is_system_user = Column(Boolean, default=False)
  api_key = Column(String(255), unique=True, index=True)
  api_key_expires = Column(DateTime)

  # Profile and preferences
  avatar_url = Column(String(1000))
  bio = Column(Text)
  social_links = Column(JSON)
  notification_preferences = Column(JSON)

  # Additional data
  custom_fields = Column(JSON)
  tags = Column(JSON)
  notes = Column(Text)

  @hybrid_property
  def is_admin(self):
    """Check if user has admin privileges."""
    return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]

  @hybrid_property
  def is_active_user(self):
    """Check if user is active and can log in."""
    return self.status == UserStatus.ACTIVE and self.email_verified

  @hybrid_property
  def can_manage_users(self):
    """Check if user can manage other users."""
    return self.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER]

  @hybrid_property
  def can_access_crm(self):
    """Check if user can access CRM features."""
    return self.role in [
        UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.MANAGER,
        UserRole.SALES_REP, UserRole.AGENT
    ]

  def set_password(self, password: str) -> None:
    """Set password with proper hashing and salt."""
    self.salt = secrets.token_hex(16)
    self.password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        self.salt.encode('utf-8'),
        100000
    ).hex()

  def verify_password(self, password: str) -> bool:
    """Verify password against stored hash."""
    password_hash_value = getattr(self, 'password_hash', None)
    salt_value = getattr(self, 'salt', None)

    if not password_hash_value or not salt_value:
      return False

    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt_value.encode('utf-8'),
        100000
    ).hex()

    return password_hash == password_hash_value

  def generate_api_key(self) -> str:
    """Generate a new API key for the user."""
    self.api_key = secrets.token_urlsafe(32)
    return self.api_key

  def __repr__(self):
    return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
