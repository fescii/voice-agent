"""
Database configuration settings
"""
import os
from pydantic import BaseModel


class DatabaseConfig(BaseModel):
  """PostgreSQL database configuration"""

  # Database connection
  host: str = "localhost"
  port: int = 5432
  username: str = "postgres"
  password: str = ""
  database: str = "voice_agents"

  # Connection pool settings
  pool_size: int = 10
  max_overflow: int = 20

  class Config:
    env_file = ".env"
    env_prefix = "DB_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.host = os.getenv("DB_HOST", self.host)
    self.port = int(os.getenv("DB_PORT", str(self.port)))
    self.username = os.getenv("DB_USERNAME", self.username)
    self.password = os.getenv("DB_PASSWORD", self.password)
    self.database = os.getenv("DB_DATABASE", self.database)

  @property
  def url(self) -> str:
    """Get database URL"""
    return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
