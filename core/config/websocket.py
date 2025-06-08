"""
WebSocket configuration settings
"""
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
