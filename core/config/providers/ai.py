"""
AI services provider configuration.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
  """Supported LLM providers."""
  OPENAI = "openai"
  ANTHROPIC = "anthropic"
  GOOGLE = "google"
  CUSTOM = "custom"


class STTProvider(Enum):
  """Supported STT providers."""
  WHISPER = "whisper"
  GOOGLE = "google"
  AZURE = "azure"
  CUSTOM = "custom"


class TTSProvider(Enum):
  """Supported TTS providers."""
  ELEVENLABS = "elevenlabs"
  OPENAI = "openai"
  GOOGLE = "google"
  AZURE = "azure"
  CUSTOM = "custom"


@dataclass
class LLMConfig:
  """LLM provider configuration."""
  provider: LLMProvider
  api_key: str
  model: str
  base_url: Optional[str] = None
  max_tokens: int = 1000
  temperature: float = 0.7
  stream: bool = True

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "provider": self.provider.value,
        "api_key": self.api_key,
        "model": self.model,
        "base_url": self.base_url,
        "max_tokens": self.max_tokens,
        "temperature": self.temperature,
        "stream": self.stream
    }


@dataclass
class STTConfig:
  """STT provider configuration."""
  provider: STTProvider
  api_key: str
  model: Optional[str] = None
  language: str = "en-US"
  sample_rate: int = 16000
  streaming: bool = True

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "provider": self.provider.value,
        "api_key": self.api_key,
        "model": self.model,
        "language": self.language,
        "sample_rate": self.sample_rate,
        "streaming": self.streaming
    }


@dataclass
class TTSConfig:
  """TTS provider configuration."""
  provider: TTSProvider
  api_key: str
  voice_id: Optional[str] = None
  model: Optional[str] = None
  speed: float = 1.0
  quality: str = "high"
  streaming: bool = True

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "provider": self.provider.value,
        "api_key": self.api_key,
        "voice_id": self.voice_id,
        "model": self.model,
        "speed": self.speed,
        "quality": self.quality,
        "streaming": self.streaming
    }
