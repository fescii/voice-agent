"""
WebSocket configuration settings
"""
import os
from pydantic import BaseModel


class WebSocketConfig(BaseModel):
  """WebSocket server configuration"""

  # Connection settings
  host: str = "0.0.0.0"
  port: int = 8080
  max_connections: int = 1000
  ping_interval: int = 20
  ping_timeout: int = 10

  # Message settings
  max_message_size: int = 1024 * 1024  # 1MB
  compression: str = "deflate"

  # Security settings
  require_auth: bool = True
  allowed_origins: list = ["*"]

  class Config:
    env_file = ".env"
    env_prefix = "WEBSOCKET_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.host = os.getenv("WEBSOCKET_HOST", self.host)
    self.port = int(os.getenv("WEBSOCKET_PORT", str(self.port)))
    self.max_connections = int(
        os.getenv("WEBSOCKET_MAX_CONNECTIONS", str(self.max_connections)))
    self.ping_interval = int(
        os.getenv("WEBSOCKET_PING_INTERVAL", str(self.ping_interval)))
    self.ping_timeout = int(
        os.getenv("WEBSOCKET_PING_TIMEOUT", str(self.ping_timeout)))
    self.max_message_size = int(
        os.getenv("WEBSOCKET_MAX_MESSAGE_SIZE", str(self.max_message_size)))
    self.require_auth = os.getenv(
        "WEBSOCKET_REQUIRE_AUTH", "true").lower() == "true"

    # Parse allowed origins from comma-separated string
    origins_str = os.getenv("WEBSOCKET_ALLOWED_ORIGINS", "*")
    if origins_str == "*":
      self.allowed_origins = ["*"]
    else:
      self.allowed_origins = [origin.strip()
                              for origin in origins_str.split(",")]
