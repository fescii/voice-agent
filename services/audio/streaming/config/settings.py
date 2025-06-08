"""
Configuration for streaming audio processing.
"""

from dataclasses import dataclass


@dataclass
class StreamingConfig:
  """Configuration for streaming audio processing."""
  buffer_size: int = 4096      # Buffer size in bytes
  chunk_duration: float = 0.1   # Chunk duration in seconds
  max_buffer_chunks: int = 100  # Maximum chunks to buffer
  silence_threshold: float = 0.01  # Silence detection threshold
  silence_timeout: float = 2.0  # Silence timeout in seconds
