"""
Streaming audio processor for real-time audio handling.
"""

import asyncio
from typing import AsyncGenerator, Optional, Callable, Dict, Any
from dataclasses import dataclass
import time
from collections import deque

from core.logging.setup import get_logger
from services.audio.processor import AudioProcessor, AudioFormat

logger = get_logger(__name__)


@dataclass
class StreamingConfig:
  """Configuration for streaming audio processing."""
  buffer_size: int = 4096      # Buffer size in bytes
  chunk_duration: float = 0.1   # Chunk duration in seconds
  max_buffer_chunks: int = 100  # Maximum chunks to buffer
  silence_threshold: float = 0.01  # Silence detection threshold
  silence_timeout: float = 2.0  # Silence timeout in seconds


class StreamingProcessor:
  """Real-time streaming audio processor."""

  def __init__(self, config: StreamingConfig, audio_processor: AudioProcessor):
    """Initialize streaming processor."""
    self.config = config
    self.audio_processor = audio_processor
    self.audio_buffer = deque(maxlen=config.max_buffer_chunks)
    self.is_processing = False
    self.last_audio_time = time.time()

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
        is_silent = await self.detect_silence(chunk, audio_format)

        if not is_silent:
          # Speech detected
          if not in_speech:
            logger.info("Speech started")
            in_speech = True
            silence_start = None

          speech_buffer.append(chunk)
          self.last_audio_time = time.time()

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


class AudioStreamService:
  """Service for managing audio streams in WebSocket connections."""

  def __init__(self):
    self.config = StreamingConfig()
    self.active_streams = {}

  async def start_stream(self, connection_id: str, audio_format: AudioFormat):
    """Start an audio stream for a connection."""
    try:
      logger.info(f"Starting audio stream for connection {connection_id}")
      # Initialize stream processor
      processor = StreamingProcessor(self.config, AudioProcessor())
      self.active_streams[connection_id] = {
          'processor': processor,
          'format': audio_format,
          'active': True
      }
      return True
    except Exception as e:
      logger.error(f"Failed to start audio stream: {e}")
      return False

  async def stop_stream(self, connection_id: str):
    """Stop an audio stream for a connection."""
    try:
      if connection_id in self.active_streams:
        stream_info = self.active_streams[connection_id]
        stream_info['active'] = False
        del self.active_streams[connection_id]
        logger.info(f"Stopped audio stream for connection {connection_id}")
      return True
    except Exception as e:
      logger.error(f"Failed to stop audio stream: {e}")
      return False

  async def process_audio_chunk(self, connection_id: str, chunk: bytes):
    """Process an audio chunk for a connection."""
    try:
      if connection_id not in self.active_streams:
        logger.warning(f"No active stream for connection {connection_id}")
        return None

      stream_info = self.active_streams[connection_id]
      processor = stream_info['processor']
      audio_format = stream_info['format']

      # Process the chunk
      processed_chunk = await processor._process_chunk(chunk, audio_format)
      return processed_chunk

    except Exception as e:
      logger.error(f"Failed to process audio chunk: {e}")
      return None

  def is_stream_active(self, connection_id: str) -> bool:
    """Check if a stream is active for a connection."""
    return connection_id in self.active_streams and self.active_streams[connection_id]['active']
