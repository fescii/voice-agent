"""
Redis configuration settings
"""
import os
from pydantic import BaseSettings


class RedisConfig(BaseSettings):
    """Redis cache configuration"""
    
    # Redis connection
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    db: int = 0
    
    # Connection settings
    max_connections: int = 10
    decode_responses: bool = True
    
    class Config:
        env_file = ".env"
        env_prefix = "REDIS_"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from environment variables
        self.host = os.getenv("REDIS_HOST", self.host)
        self.port = int(os.getenv("REDIS_PORT", str(self.port)))
        self.password = os.getenv("REDIS_PASSWORD", self.password)
        self.db = int(os.getenv("REDIS_DB", str(self.db)))
        
    @property
    def url(self) -> str:
        """Get Redis URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
