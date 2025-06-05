"""
OpenAI Whisper Speech-to-Text service implementation.
"""

import asyncio
from typing import Optional, Dict, Any, Union
import httpx
from io import BytesIO
import tempfile
import os

from core.config.services.stt.whisper import WhisperConfig
from core.logging import get_logger

logger = get_logger(__name__)


class WhisperService:
  """OpenAI Whisper STT service for converting speech to text."""

  def __init__(self, config: WhisperConfig):
    """Initialize Whisper service."""
    self.config = config
    self.client = httpx.AsyncClient(
        base_url=config.base_url,
        headers={
            "Authorization": f"Bearer {config.api_key}",
        },
        timeout=60.0  # Longer timeout for audio processing
    )

  async def transcribe_audio(
      self,
      audio_data: bytes,
      file_format: str = "wav",
      language: Optional[str] = None,
      prompt: Optional[str] = None,
      response_format: str = "json",
      temperature: float = 0.0
  ) -> Dict[str, Any]:
    """
    Transcribe audio to text.

    Args:
        audio_data: Audio data as bytes
        file_format: Audio file format (wav, mp3, m4a, etc.)
        language: Language code (ISO-639-1)
        prompt: Optional prompt to guide the model
        response_format: Response format (json, text, srt, verbose_json, vtt)
        temperature: Sampling temperature (0.0 to 1.0)

    Returns:
        Transcription result
    """
    try:
      logger.info(
          f"Transcribing audio ({len(audio_data)} bytes, format: {file_format})")

      # Create temporary file for audio data
      with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as temp_file:
        temp_file.write(audio_data)
        temp_file_path = temp_file.name

      try:
        # Prepare form data
        with open(temp_file_path, 'rb') as audio_file:
          files = {
              "file": (f"audio.{file_format}", audio_file, f"audio/{file_format}")
          }

          data = {
              "model": self.config.model,
              "response_format": response_format,
              "temperature": temperature
          }

          if language:
            data["language"] = language

          if prompt:
            data["prompt"] = prompt

          response = await self.client.post(
              "/audio/transcriptions",
              files=files,
              data=data
          )
          response.raise_for_status()

        if response_format == "json" or response_format == "verbose_json":
          result = response.json()
        else:
          result = {"text": response.text}

        logger.info(
            f"Successfully transcribed audio: {len(result.get('text', ''))} characters")
        return result

      finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
          os.unlink(temp_file_path)

    except httpx.HTTPStatusError as e:
      logger.error(
          f"Whisper API error: {e.response.status_code} - {e.response.text}")
      raise
    except Exception as e:
      logger.error(f"Error transcribing audio: {str(e)}")
      raise

  async def translate_audio(
      self,
      audio_data: bytes,
      file_format: str = "wav",
      prompt: Optional[str] = None,
      response_format: str = "json",
      temperature: float = 0.0
  ) -> Dict[str, Any]:
    """
    Translate audio to English text.

    Args:
        audio_data: Audio data as bytes
        file_format: Audio file format
        prompt: Optional prompt to guide the model
        response_format: Response format
        temperature: Sampling temperature

    Returns:
        Translation result
    """
    try:
      logger.info(
          f"Translating audio ({len(audio_data)} bytes, format: {file_format})")

      # Create temporary file for audio data
      with tempfile.NamedTemporaryFile(suffix=f".{file_format}", delete=False) as temp_file:
        temp_file.write(audio_data)
        temp_file_path = temp_file.name

      try:
        # Prepare form data
        with open(temp_file_path, 'rb') as audio_file:
          files = {
              "file": (f"audio.{file_format}", audio_file, f"audio/{file_format}")
          }

          data = {
              "model": self.config.model,
              "response_format": response_format,
              "temperature": temperature
          }

          if prompt:
            data["prompt"] = prompt

          response = await self.client.post(
              "/audio/translations",
              files=files,
              data=data
          )
          response.raise_for_status()

        if response_format == "json" or response_format == "verbose_json":
          result = response.json()
        else:
          result = {"text": response.text}

        logger.info(
            f"Successfully translated audio: {len(result.get('text', ''))} characters")
        return result

      finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
          os.unlink(temp_file_path)

    except httpx.HTTPStatusError as e:
      logger.error(
          f"Whisper translation API error: {e.response.status_code} - {e.response.text}")
      raise
    except Exception as e:
      logger.error(f"Error translating audio: {str(e)}")
      raise

  async def transcribe_streaming(
      self,
      audio_chunks: list[bytes],
      file_format: str = "wav",
      language: Optional[str] = None,
      prompt: Optional[str] = None
  ) -> str:
    """
    Transcribe streaming audio chunks.

    Args:
        audio_chunks: List of audio data chunks
        file_format: Audio file format
        language: Language code
        prompt: Optional prompt

    Returns:
        Transcribed text
    """
    try:
      # Combine audio chunks
      combined_audio = b"".join(audio_chunks)

      logger.info(
          f"Transcribing streaming audio ({len(combined_audio)} bytes from {len(audio_chunks)} chunks)")

      result = await self.transcribe_audio(
          audio_data=combined_audio,
          file_format=file_format,
          language=language,
          prompt=prompt,
          response_format="json"
      )

      return result.get("text", "")

    except Exception as e:
      logger.error(f"Error transcribing streaming audio: {str(e)}")
      raise

  async def detect_language(self, audio_data: bytes, file_format: str = "wav") -> str:
    """
    Detect the language of audio.

    Args:
        audio_data: Audio data as bytes
        file_format: Audio file format

    Returns:
        Detected language code
    """
    try:
      # Use verbose_json to get language information
      result = await self.transcribe_audio(
          audio_data=audio_data,
          file_format=file_format,
          response_format="verbose_json"
      )

      detected_language = result.get("language", "unknown")
      logger.info(f"Detected language: {detected_language}")

      return detected_language

    except Exception as e:
      logger.error(f"Error detecting language: {str(e)}")
      raise

  async def get_supported_formats(self) -> list[str]:
    """
    Get list of supported audio formats.

    Returns:
        List of supported file formats
    """
    # Based on OpenAI Whisper documentation
    return [
        "flac", "m4a", "mp3", "mp4", "mpeg", "mpga",
        "oga", "ogg", "wav", "webm"
    ]

  async def validate_audio_format(self, file_format: str) -> bool:
    """
    Validate if audio format is supported.

    Args:
        file_format: Audio file format to validate

    Returns:
        True if format is supported
    """
    supported_formats = await self.get_supported_formats()
    return file_format.lower() in supported_formats

  async def close(self):
    """Close the HTTP client."""
    await self.client.aclose()

  async def __aenter__(self):
    """Async context manager entry."""
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit."""
    await self.close()
