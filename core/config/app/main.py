"""
Main application configuration
"""
import os
from pydantic import BaseSettings


class AppConfig(BaseSettings):
    """Application configuration settings"""
    
    app_name: str = "AI Voice Agent System"
    version: str = "1.0.0"
    debug_mode: bool = False
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    
    class Config:
        env_file = ".env"
        env_prefix = "APP_"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from environment variables
        self.debug_mode = os.getenv("APP_DEBUG_MODE", "false").lower() == "true"
        self.secret_key = os.getenv("APP_SECRET_KEY", self.secret_key)
