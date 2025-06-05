"""
ElevenLabs TTS API configuration settings
"""
import os
from pydantic import BaseModel


class ElevenLabsConfig(BaseModel):
  """ElevenLabs TTS API configuration"""

  # API settings
  api_key: str = ""
  base_url: str = "https://api.elevenlabs.io/v1"
  voice_id: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
  model_id: str = "eleven_flash_v2_5"  # Low-latency model

  # Audio settings
  optimize_streaming_latency: int = 1
  output_format: str = "pcm_16000"

  class Config:
    env_file = ".env"
    env_prefix = "ELEVENLABS_"

  def __init__(self, **kwargs):
    super().__init__(**kwargs)
    # Load from environment variables
    self.api_key = os.getenv("ELEVENLABS_API_KEY", self.api_key)
    self.base_url = os.getenv("ELEVENLABS_BASE_URL", self.base_url)
    self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", self.voice_id)
    self.model_id = os.getenv("ELEVENLABS_MODEL_ID", self.model_id)
