"""
Email notification configuration settings
"""
import os
from pydantic_settings import BaseSettings


class EmailConfig(BaseSettings):
  """Email notification configuration"""

  # SMTP settings
  smtp_host: str = "localhost"
  smtp_port: int = 587
  smtp_user: str = ""
  smtp_password: str = ""
  smtp_use_tls: bool = True
  smtp_use_ssl: bool = False

  # Email settings
  from_email: str = ""
  from_name: str = "Voice Agent System"

  class Config:
    env_file = ".env"
    env_prefix = "EMAIL_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.smtp_host = os.getenv("EMAIL_SMTP_HOST", self.smtp_host)
    self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", str(self.smtp_port)))
    self.smtp_user = os.getenv("EMAIL_SMTP_USER", self.smtp_user)
    self.smtp_password = os.getenv("EMAIL_SMTP_PASSWORD", self.smtp_password)
    self.from_email = os.getenv("EMAIL_FROM_EMAIL", self.from_email)
    self.from_name = os.getenv("EMAIL_FROM_NAME", self.from_name)
