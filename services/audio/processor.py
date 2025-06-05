"""
Audio processing service for format conversion and quality enhancement.
"""

import asyncio
from typing import Optional, Dict, Any, Tuple
import io
import wave
import audioop
from dataclasses import dataclass

from core.logging.setup import get_logger

logger = get_logger(__name__)


@dataclass
class AudioFormat:
  """Audio format specification."""
  sample_rate: int
  channels: int
  sample_width: int  # bytes per sample
  format: str  # wav, mp3, etc.


class AudioProcessor:
  """Service for processing and converting audio data."""

  def __init__(self):
    """Initialize audio processor."""
    self.supported_formats = ["wav", "mp3", "m4a", "ogg", "flac"]
    self.target_format = AudioFormat(
        sample_rate=16000,  # 16kHz for optimal speech processing
        channels=1,         # Mono
        sample_width=2,     # 16-bit
        format="wav"
    )

  async def normalize_audio(
      self,
      audio_data: bytes,
      source_format: AudioFormat,
      target_format: Optional[AudioFormat] = None
  ) -> Tuple[bytes, AudioFormat]:
    """
    Normalize audio to target format.

    Args:
        audio_data: Raw audio data
        source_format: Source audio format
        target_format: Target format (defaults to standard format)

    Returns:
        Tuple of (normalized_audio_data, actual_format)
    """
    target_format = target_format or self.target_format

    try:
      logger.info(f"Normalizing audio from {source_format} to {target_format}")

      # Convert to target sample rate
      if source_format.sample_rate != target_format.sample_rate:
        audio_data, _ = audioop.ratecv(
            audio_data,
            source_format.sample_width,
            source_format.channels,
            source_format.sample_rate,
            target_format.sample_rate,
            None
        )

      # Convert to target channels (mono/stereo)
      if source_format.channels != target_format.channels:
        if source_format.channels == 2 and target_format.channels == 1:
          # Stereo to mono
          audio_data = audioop.tomono(
              audio_data, source_format.sample_width, 1, 1)
        elif source_format.channels == 1 and target_format.channels == 2:
          # Mono to stereo
          audio_data = audioop.tostereo(
              audio_data, source_format.sample_width, 1, 1)

      # Convert sample width
      if source_format.sample_width != target_format.sample_width:
        audio_data = audioop.lin2lin(
            audio_data,
            source_format.sample_width,
            target_format.sample_width
        )

      logger.info(f"Normalized audio: {len(audio_data)} bytes")
      return audio_data, target_format

    except Exception as e:
      logger.error(f"Error normalizing audio: {str(e)}")
      raise

  async def enhance_audio_quality(
      self,
      audio_data: bytes,
      audio_format: AudioFormat,
      noise_reduction: bool = True,
      volume_normalization: bool = True
  ) -> bytes:
    """
    Enhance audio quality.

    Args:
        audio_data: Raw audio data
        audio_format: Audio format
        noise_reduction: Apply noise reduction
        volume_normalization: Normalize volume

    Returns:
        Enhanced audio data
    """
    try:
      logger.info("Enhancing audio quality")
      enhanced_data = audio_data

      # Volume normalization
      if volume_normalization:
        enhanced_data = await self._normalize_volume(enhanced_data, audio_format)

      # Basic noise reduction (simple high-pass filter simulation)
      if noise_reduction:
        enhanced_data = await self._reduce_noise(enhanced_data, audio_format)

      logger.info("Audio quality enhancement completed")
      return enhanced_data

    except Exception as e:
      logger.error(f"Error enhancing audio quality: {str(e)}")
      raise

  async def _normalize_volume(self, audio_data: bytes, audio_format: AudioFormat) -> bytes:
    """Normalize audio volume."""
    try:
      # Get max amplitude
      max_amp = audioop.max(audio_data, audio_format.sample_width)

      if max_amp == 0:
        return audio_data

      # Calculate normalization factor (target 80% of max)
      max_possible = (2 ** (audio_format.sample_width * 8 - 1)) - 1
      target_max = int(max_possible * 0.8)
      factor = target_max / max_amp

      # Apply normalization
      if factor != 1.0:
        normalized_data = audioop.mul(
            audio_data, audio_format.sample_width, factor)
        logger.debug(f"Volume normalized with factor: {factor:.2f}")
        return normalized_data

      return audio_data

    except Exception as e:
      logger.warning(f"Volume normalization failed: {str(e)}")
      return audio_data

  async def _reduce_noise(self, audio_data: bytes, audio_format: AudioFormat) -> bytes:
    """Apply basic noise reduction."""
    try:
      # Simple noise reduction using bias removal
      # This is a basic implementation - for production, consider using
      # more sophisticated noise reduction libraries

      bias = audioop.avg(audio_data, audio_format.sample_width)
      if bias != 0:
        # Remove DC bias
        debiased_data = audioop.bias(
            audio_data, audio_format.sample_width, -bias)
        logger.debug(f"Removed DC bias: {bias}")
        return debiased_data

      return audio_data

    except Exception as e:
      logger.warning(f"Noise reduction failed: {str(e)}")
      return audio_data

  async def convert_to_wav(
      self,
      audio_data: bytes,
      audio_format: AudioFormat
  ) -> bytes:
    """
    Convert audio data to WAV format.

    Args:
        audio_data: Raw audio data
        audio_format: Audio format specification

    Returns:
        WAV formatted audio data
    """
    try:
      # Create WAV file in memory
      wav_buffer = io.BytesIO()

      with wave.open(wav_buffer, 'wb') as wav_file:
        wav_file.setnchannels(audio_format.channels)
        wav_file.setsampwidth(audio_format.sample_width)
        wav_file.setframerate(audio_format.sample_rate)
        wav_file.writeframes(audio_data)

      wav_data = wav_buffer.getvalue()
      logger.info(f"Converted to WAV: {len(wav_data)} bytes")

      return wav_data

    except Exception as e:
      logger.error(f"Error converting to WAV: {str(e)}")
      raise

  async def extract_audio_info(self, audio_data: bytes) -> Dict[str, Any]:
    """
    Extract information from audio data.

    Args:
        audio_data: Audio data to analyze

    Returns:
        Dictionary with audio information
    """
    try:
      # Try to parse as WAV first
      wav_buffer = io.BytesIO(audio_data)

      try:
        with wave.open(wav_buffer, 'rb') as wav_file:
          info = {
              "format": "wav",
              "channels": wav_file.getnchannels(),
              "sample_width": wav_file.getsampwidth(),
              "sample_rate": wav_file.getframerate(),
              "frames": wav_file.getnframes(),
              "duration": wav_file.getnframes() / wav_file.getframerate()
          }

          logger.info(f"Extracted audio info: {info}")
          return info

      except wave.Error:
        # Not a valid WAV file
        logger.warning("Could not parse as WAV file")

        # Return basic info
        return {
            "format": "unknown",
            "size_bytes": len(audio_data),
            "channels": None,
            "sample_width": None,
            "sample_rate": None,
            "duration": None
        }

    except Exception as e:
      logger.error(f"Error extracting audio info: {str(e)}")
      raise

  async def split_audio_chunks(
      self,
      audio_data: bytes,
      audio_format: AudioFormat,
      chunk_duration: float = 30.0
  ) -> list[bytes]:
    """
    Split audio into chunks of specified duration.

    Args:
        audio_data: Audio data to split
        audio_format: Audio format
        chunk_duration: Duration of each chunk in seconds

    Returns:
        List of audio chunks
    """
    try:
      bytes_per_second = (
          audio_format.sample_rate *
          audio_format.channels *
          audio_format.sample_width
      )

      chunk_size = int(bytes_per_second * chunk_duration)

      # Ensure chunk size is frame-aligned
      frame_size = audio_format.channels * audio_format.sample_width
      chunk_size = (chunk_size // frame_size) * frame_size

      chunks = []
      for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i:i + chunk_size]
        if len(chunk) > 0:
          chunks.append(chunk)

      logger.info(
          f"Split audio into {len(chunks)} chunks of ~{chunk_duration}s each")
      return chunks

    except Exception as e:
      logger.error(f"Error splitting audio: {str(e)}")
      raise

  async def validate_audio_format(self, format_name: str) -> bool:
    """
    Validate if audio format is supported.

    Args:
        format_name: Audio format name

    Returns:
        True if format is supported
    """
    return format_name.lower() in self.supported_formats
