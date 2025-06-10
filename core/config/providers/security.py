"""
Security and authentication configuration.
"""
import os
from pydantic import BaseModel
from typing import Optional


class SecurityConfig(BaseModel):
  """Security and authentication configuration."""

  # Password hashing
  password_salt: str = "default_salt_change_in_production"
  password_rounds: int = 12

  # JWT configuration
  jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
  jwt_algorithm: str = "HS256"
  jwt_access_token_expire_minutes: int = 30
  jwt_refresh_token_expire_days: int = 7

  # Session configuration
  session_secret_key: str = "your-session-secret-key-change-in-production"
  session_cookie_name: str = "voice_agent_session"
  session_expire_hours: int = 24

  # API key configuration
  api_key_header: str = "X-API-Key"
  api_key_expire_days: int = 365

  # Rate limiting
  rate_limit_per_minute: int = 60
  rate_limit_per_hour: int = 1000

  # CORS settings
  cors_origins: str = "*"
  cors_methods: str = "GET,POST,PUT,DELETE,OPTIONS"
  cors_headers: str = "*"

  class Config:
    env_file = ".env"
    env_prefix = "SECURITY_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.password_salt = os.getenv(
        "SECURITY_PASSWORD_SALT", self.password_salt)
    self.password_rounds = int(
        os.getenv("SECURITY_PASSWORD_ROUNDS", str(self.password_rounds)))

    self.jwt_secret_key = os.getenv(
        "SECURITY_JWT_SECRET_KEY", self.jwt_secret_key)
    self.jwt_algorithm = os.getenv(
        "SECURITY_JWT_ALGORITHM", self.jwt_algorithm)
    self.jwt_access_token_expire_minutes = int(os.getenv(
        "SECURITY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES", str(self.jwt_access_token_expire_minutes)))
    self.jwt_refresh_token_expire_days = int(os.getenv(
        "SECURITY_JWT_REFRESH_TOKEN_EXPIRE_DAYS", str(self.jwt_refresh_token_expire_days)))

    self.session_secret_key = os.getenv(
        "SECURITY_SESSION_SECRET_KEY", self.session_secret_key)
    self.session_cookie_name = os.getenv(
        "SECURITY_SESSION_COOKIE_NAME", self.session_cookie_name)
    self.session_expire_hours = int(
        os.getenv("SECURITY_SESSION_EXPIRE_HOURS", str(self.session_expire_hours)))

    self.api_key_header = os.getenv(
        "SECURITY_API_KEY_HEADER", self.api_key_header)
    self.api_key_expire_days = int(
        os.getenv("SECURITY_API_KEY_EXPIRE_DAYS", str(self.api_key_expire_days)))

    self.rate_limit_per_minute = int(
        os.getenv("SECURITY_RATE_LIMIT_PER_MINUTE", str(self.rate_limit_per_minute)))
    self.rate_limit_per_hour = int(
        os.getenv("SECURITY_RATE_LIMIT_PER_HOUR", str(self.rate_limit_per_hour)))

    self.cors_origins = os.getenv("SECURITY_CORS_ORIGINS", self.cors_origins)
    self.cors_methods = os.getenv("SECURITY_CORS_METHODS", self.cors_methods)
    self.cors_headers = os.getenv("SECURITY_CORS_HEADERS", self.cors_headers)
