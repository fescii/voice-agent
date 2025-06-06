"""
Ringover API configuration settings
"""
import os
from pydantic import BaseModel


class RingoverConfig(BaseModel):
  """Ringover API configuration"""

  # API settings
  api_key: str = ""
  api_base_url: str = "https://public-api.ringover.com/v2.1"

  # Default caller ID for outbound calls
  default_caller_id: str = ""

  # Webhook settings
  webhook_secret: str = ""
  webhook_base_url: str = ""

  # Media streaming settings
  streamer_auth_token: str = ""

  class Config:
    env_file = ".env"
    env_prefix = "RINGOVER_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.api_key = os.getenv("RINGOVER_API_KEY", self.api_key)
    self.default_caller_id = os.getenv(
        "RINGOVER_DEFAULT_CALLER_ID", self.default_caller_id)
    self.webhook_secret = os.getenv(
        "RINGOVER_WEBHOOK_SECRET", self.webhook_secret)
    self.webhook_base_url = os.getenv(
        "RINGOVER_WEBHOOK_BASE_URL", self.webhook_base_url)
    self.streamer_auth_token = os.getenv(
        "RINGOVER_STREAMER_AUTH_TOKEN", self.streamer_auth_token)
