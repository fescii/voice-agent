"""
Voice activity detection for streaming audio.
"""

import time
from typing import AsyncGenerator, Callable, Optional

from core.logging.setup import get_logger
from services.audio.processor import AudioFormat
from .silence import SilenceDetector
from ..config import StreamingConfig

logger = get_logger(__name__)


class VoiceActivityDetector:
  """Handles voice activity detection in audio streams."""

  def __init__(self, config: StreamingConfig):
    """Initialize voice activity detector."""
    self.config = config
    self.silence_detector = SilenceDetector(config)

  async def start_voice_activity_detection(
      self,
      audio_stream: AsyncGenerator[bytes, None],
      audio_format: AudioFormat,
      speech_callback: Callable[[bytes], None],
      silence_callback: Optional[Callable[[], None]] = None
  ):
    """
    Start voice activity detection on audio stream.

    Args:
        audio_stream: Stream of audio chunks
        audio_format: Audio format
        speech_callback: Callback when speech is detected
        silence_callback: Callback when silence timeout is reached
    """
    try:
      logger.info("Starting voice activity detection")

      speech_buffer = []
      in_speech = False
      silence_start = None

      async for chunk in audio_stream:
        is_silent = await self.silence_detector.detect_silence(chunk, audio_format)

        if not is_silent:
          # Speech detected
          if not in_speech:
            logger.info("Speech started")
            in_speech = True
            silence_start = None

          speech_buffer.append(chunk)
          self.silence_detector.update_audio_time()

        else:
          # Silence detected
          if in_speech:
            if silence_start is None:
              silence_start = time.time()

            # Check if silence duration exceeds threshold
            silence_duration = time.time() - silence_start
            if silence_duration > self.config.silence_timeout:
              # End of speech
              logger.info(
                  f"Speech ended after {silence_duration:.2f}s silence")

              if speech_buffer:
                combined_speech = b"".join(speech_buffer)
                speech_callback(combined_speech)
                speech_buffer.clear()

              in_speech = False
              silence_start = None

              if silence_callback:
                silence_callback()

    except Exception as e:
      logger.error(f"Error in voice activity detection: {str(e)}")
      raise
