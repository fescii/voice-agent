"""
Core streaming audio processor.
"""

import asyncio
from typing import AsyncGenerator, Optional, Callable, Dict, Any
import time
from collections import deque

from core.logging.setup import get_logger
from services.audio.processor import AudioProcessor, AudioFormat
from ..config import StreamingConfig
from .silence import SilenceDetector
from .vad import VoiceActivityDetector

logger = get_logger(__name__)


class StreamingProcessor:
  """Real-time streaming audio processor."""

  def __init__(self, config: StreamingConfig, audio_processor: AudioProcessor):
    """Initialize streaming processor."""
    self.config = config
    self.audio_processor = audio_processor
    self.audio_buffer = deque(maxlen=config.max_buffer_chunks)
    self.is_processing = False
    self.last_audio_time = time.time()
    self.silence_detector = SilenceDetector(config)
    self.vad = VoiceActivityDetector(config)

  async def process_audio_stream(
      self,
      audio_stream: AsyncGenerator[bytes, None],
      audio_format: AudioFormat,
      callback: Optional[Callable[[bytes], None]] = None
  ) -> AsyncGenerator[bytes, None]:
    """
    Process streaming audio data.

    Args:
        audio_stream: Async generator of audio chunks
        audio_format: Audio format specification
        callback: Optional callback for processed chunks

    Yields:
        Processed audio chunks
    """
    try:
      logger.info("Starting streaming audio processing")
      self.is_processing = True

      async for chunk in audio_stream:
        if not self.is_processing:
          break

        # Add to buffer
        self.audio_buffer.append(chunk)
        self.last_audio_time = time.time()

        # Process buffered chunks
        processed_chunk = await self._process_chunk(chunk, audio_format)

        if processed_chunk:
          if callback:
            callback(processed_chunk)
          yield processed_chunk

    except Exception as e:
      logger.error(f"Error in streaming processing: {str(e)}")
      raise
    finally:
      self.is_processing = False
      logger.info("Stopped streaming audio processing")

  async def _process_chunk(self, chunk: bytes, audio_format: AudioFormat) -> Optional[bytes]:
    """Process a single audio chunk."""
    try:
      # Basic processing - normalize and enhance
      processed_chunk = chunk

      # Normalize the chunk
      if len(chunk) > 0:
        normalized_chunk, _ = await self.audio_processor.normalize_audio(
            chunk, audio_format, self.audio_processor.target_format
        )
        processed_chunk = normalized_chunk

      return processed_chunk

    except Exception as e:
      logger.warning(f"Error processing chunk: {str(e)}")
      return chunk  # Return original chunk if processing fails

  async def detect_silence(self, chunk: bytes, audio_format: AudioFormat) -> bool:
    """
    Detect if audio chunk contains silence.
    Delegates to silence detector.
    """
    return await self.silence_detector.detect_silence(chunk, audio_format)

  async def check_silence_timeout(self) -> bool:
    """
    Check if silence timeout has been reached.
    Delegates to silence detector.
    """
    return await self.silence_detector.check_silence_timeout()

  async def start_voice_activity_detection(
      self,
      audio_stream: AsyncGenerator[bytes, None],
      audio_format: AudioFormat,
      speech_callback: Callable[[bytes], None],
      silence_callback: Optional[Callable[[], None]] = None
  ):
    """
    Start voice activity detection on audio stream.
    Delegates to VAD.
    """
    return await self.vad.start_voice_activity_detection(
        audio_stream, audio_format, speech_callback, silence_callback
    )

  async def get_buffered_audio(self) -> bytes:
    """
    Get all buffered audio as a single chunk.

    Returns:
        Combined audio data from buffer
    """
    try:
      if not self.audio_buffer:
        return b""

      combined_audio = b"".join(self.audio_buffer)
      logger.info(
          f"Retrieved {len(combined_audio)} bytes from buffer ({len(self.audio_buffer)} chunks)")

      return combined_audio

    except Exception as e:
      logger.error(f"Error getting buffered audio: {str(e)}")
      return b""

  async def clear_buffer(self):
    """Clear the audio buffer."""
    self.audio_buffer.clear()
    logger.debug("Audio buffer cleared")

  def stop_processing(self):
    """Stop all processing."""
    self.is_processing = False
    logger.info("Streaming processor stopped")

  async def get_stream_stats(self) -> Dict[str, Any]:
    """
    Get streaming statistics.

    Returns:
        Dictionary with streaming stats
    """
    current_time = time.time()
    return {
        "is_processing": self.is_processing,
        "buffer_size": len(self.audio_buffer),
        "max_buffer_size": self.config.max_buffer_chunks,
        "last_audio_time": self.last_audio_time,
        "silence_duration": current_time - self.last_audio_time,
        "silence_timeout": self.config.silence_timeout
    }
