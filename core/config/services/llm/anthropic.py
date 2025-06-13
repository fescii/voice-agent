"""
Anthropic Claud  class Config:
    env_file = ".env"
    env_prefix = "ANTHROPIC_"figuration settings
"""
import os
from pydantic import BaseModel


class AnthropicConfig(BaseModel):
  """Anthropic Claude API configuration"""

  # API settings
  api_key: str = ""
  model: str = "claude-3-sonnet-20240229"
  max_tokens: int = 1000
  temperature: float = 0.7

  # Streaming settings
  stream: bool = True

  class Config:
    env_file = ".env"
    env_prefix = "ANTHROPIC_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.api_key = os.getenv("ANTHROPIC_API_KEY", self.api_key)
    self.model = os.getenv("ANTHROPIC_MODEL", self.model)
