"""
Silence detection functionality for streaming audio.
"""

import time
from typing import Optional, Callable

from core.logging.setup import get_logger
from services.audio.processor import AudioFormat
from ..config import StreamingConfig

logger = get_logger(__name__)


class SilenceDetector:
  """Handles silence detection in audio streams."""

  def __init__(self, config: StreamingConfig):
    """Initialize silence detector."""
    self.config = config
    self.last_audio_time = time.time()

  async def detect_silence(self, chunk: bytes, audio_format: AudioFormat) -> bool:
    """
    Detect if audio chunk contains silence.

    Args:
        chunk: Audio chunk to analyze
        audio_format: Audio format

    Returns:
        True if chunk is silent
    """
    try:
      if len(chunk) == 0:
        return True

      # Calculate RMS (Root Mean Square) for volume detection
      sample_count = len(chunk) // audio_format.sample_width
      if sample_count == 0:
        return True

      # Simple silence detection based on amplitude
      # This is a basic implementation
      total = 0
      for i in range(0, len(chunk), audio_format.sample_width):
        if i + audio_format.sample_width <= len(chunk):
          sample = int.from_bytes(
              chunk[i:i + audio_format.sample_width],
              byteorder='little',
              signed=True
          )
          total += sample * sample

      rms = (total / sample_count) ** 0.5
      max_amplitude = (2 ** (audio_format.sample_width * 8 - 1)) - 1
      normalized_rms = rms / max_amplitude

      is_silent = normalized_rms < self.config.silence_threshold

      if is_silent:
        logger.debug(f"Silence detected (RMS: {normalized_rms:.4f})")

      return is_silent

    except Exception as e:
      logger.warning(f"Error detecting silence: {str(e)}")
      return False

  async def check_silence_timeout(self) -> bool:
    """
    Check if silence timeout has been reached.

    Returns:
        True if silence timeout exceeded
    """
    current_time = time.time()
    silence_duration = current_time - self.last_audio_time

    timeout_exceeded = silence_duration > self.config.silence_timeout

    if timeout_exceeded:
      logger.info(f"Silence timeout exceeded: {silence_duration:.2f}s")

    return timeout_exceeded

  def update_audio_time(self):
    """Update the last audio time."""
    self.last_audio_time = time.time()
