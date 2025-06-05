"""
Google Gemini API configuration settings
"""
import os
from pydantic import BaseSettings


class GeminiConfig(BaseSettings):
  """Google Gemini API configuration"""

  # API settings
  api_key: str = ""
  model: str = "gemini-pro"
  max_tokens: int = 1000
  temperature: float = 0.7

  # Streaming settings
  stream: bool = True

  class Config:
    env_file = ".env"
    env_prefix = "GEMINI_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.api_key = os.getenv("GEMINI_API_KEY", self.api_key)
    self.model = os.getenv("GEMINI_MODEL", self.model)
