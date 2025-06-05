"""
OpenAI API configuration settings
"""
import os
from pydantic_settings import BaseSettings


class OpenAIConfig(BaseSettings):
  """OpenAI API configuration"""

  # API settings
  api_key: str = ""
  base_url: str = "https://api.openai.com/v1"
  model: str = "gpt-4o"
  max_tokens: int = 1000
  temperature: float = 0.7

  # Streaming settings
  stream: bool = True

  class Config:
    env_file = ".env"
    env_prefix = "OPENAI_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.api_key = os.getenv("OPENAI_API_KEY", self.api_key)
    self.base_url = os.getenv("OPENAI_BASE_URL", self.base_url)
    self.model = os.getenv("OPENAI_MODEL", self.model)
