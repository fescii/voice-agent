"""
OpenAI Whisper STT API configuration settings
"""
import os
from pydantic import BaseSettings


class WhisperConfig(BaseSettings):
    """OpenAI Whisper STT API configuration"""
    
    # API settings
    api_key: str = ""
    model: str = "whisper-1"
    
    # Audio settings
    language: str = "en"
    response_format: str = "json"
    temperature: float = 0.0
    
    class Config:
        env_file = ".env"
        env_prefix = "WHISPER_"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load from environment variables
        self.api_key = os.getenv("WHISPER_API_KEY", self.api_key)
        self.model = os.getenv("WHISPER_MODEL", self.model)
