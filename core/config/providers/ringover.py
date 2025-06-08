"""
Ringover API configuration settings
"""
import os
from pydantic import BaseModel


class RingoverConfig(BaseModel):
  """Ringover API configuration"""

  # API settings
  api_key: str = ""
  api_base_url: str = ""

  # Default caller ID for outbound calls
  default_caller_id: str = ""

  # Webhook settings
  webhook_secret: str = ""
  webhook_url: str = ""

  # Media streaming settings
  streamer_auth_token: str = ""
  websocket_url: str = ""

  class Config:
    env_file = ".env"
    env_prefix = "RINGOVER_"
