"""
Audio streaming models and data structures.
"""
from typing import Optional, Callable, Awaitable, Dict, Any
from dataclasses import dataclass


@dataclass
class AudioFrame:
  """Audio frame data structure."""
  call_id: str
  audio_data: bytes
  format: str = "pcm"
  sample_rate: int = 16000
  channels: int = 1
  timestamp: Optional[float] = None


# Type aliases for handlers
AudioHandler = Callable[[AudioFrame], Awaitable[Optional[bytes]]]
EventHandler = Callable[[Dict[str, Any]], Awaitable[None]]
