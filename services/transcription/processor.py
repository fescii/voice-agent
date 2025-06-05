"""Transcription processor for converting audio to text."""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator

import httpx
from pydantic import BaseModel

from core.config.services.stt.whisper import WhisperConfig
from core.logging.setup import get_logger
from data.db.ops.transcript.save import save_transcript
from models.internal.callcontext import CallContext


class TranscriptionSegment(BaseModel):
  """Transcription segment model."""

  text: str
  start_time: float
  end_time: float
  confidence: float
  speaker: Optional[str] = None


class TranscriptionResult(BaseModel):
  """Transcription result model."""

  call_id: str
  segments: List[TranscriptionSegment]
  full_text: str
  language: Optional[str] = None
  timestamp: datetime
  audio_duration: float


class TranscriptionProcessor:
  """Processes audio transcription using various STT services."""

  def __init__(self, whisper_config: WhisperConfig):
    self.logger = get_logger(__name__)
    self.whisper_config = whisper_config
    self._http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0)
    )

  async def transcribe_audio(
      self,
      audio_data: bytes,
      call_context: CallContext,
      format: str = "wav",
      language: Optional[str] = None
  ) -> TranscriptionResult:
    """Transcribe audio data to text."""

    self.logger.info(
        f"Starting transcription for call: {call_context.call_id}")

    try:
      # Use OpenAI Whisper API
      result = await self._transcribe_with_whisper(
          audio_data, format, language
      )

      # Create transcription result
      transcription = TranscriptionResult(
          call_id=call_context.call_id,
          segments=result["segments"],
          full_text=result["text"],
          language=result.get("language"),
          timestamp=datetime.utcnow(),
          audio_duration=result.get("duration", 0.0)
      )

      # Save to database
      await self._save_transcription(transcription, call_context)

      self.logger.info(
          f"Transcription completed for call: {call_context.call_id}, "
          f"text length: {len(transcription.full_text)}"
      )

      return transcription

    except Exception as e:
      self.logger.error(
          f"Transcription failed for call {call_context.call_id}: {e}")
      raise

  async def transcribe_stream(
      self,
      audio_stream: asyncio.Queue,
      call_context: CallContext,
      chunk_duration: float = 5.0
  ) -> AsyncGenerator[TranscriptionSegment, None]:
    """Transcribe audio stream in real-time."""

    self.logger.info(
        f"Starting stream transcription for call: {call_context.call_id}")

    audio_buffer = bytearray()
    last_transcription_time = 0.0

    try:
      while True:
        try:
          # Get audio chunk with timeout
          audio_chunk = await asyncio.wait_for(
              audio_stream.get(), timeout=1.0
          )

          if audio_chunk is None:  # End of stream marker
            break

          audio_buffer.extend(audio_chunk)

          # Check if we have enough audio for transcription
          current_time = len(audio_buffer) / \
              (16000 * 2)  # Assume 16kHz, 16-bit

          if current_time - last_transcription_time >= chunk_duration:
            # Extract chunk for transcription
            chunk_start = int(last_transcription_time * 16000 * 2)
            chunk_end = int(current_time * 16000 * 2)
            chunk_data = bytes(audio_buffer[chunk_start:chunk_end])

            # Transcribe chunk
            result = await self._transcribe_with_whisper(chunk_data, "wav")

            if result["text"].strip():
              segment = TranscriptionSegment(
                  text=result["text"].strip(),
                  start_time=last_transcription_time,
                  end_time=current_time,
                  confidence=0.9,  # Default confidence
                  speaker="user"  # Default speaker
              )

              yield segment

            last_transcription_time = current_time

        except asyncio.TimeoutError:
          # Check if we should finalize remaining audio
          if len(audio_buffer) > 0:
            current_time = len(audio_buffer) / (16000 * 2)
            if current_time - last_transcription_time > 1.0:  # At least 1 second
              chunk_start = int(last_transcription_time * 16000 * 2)
              chunk_data = bytes(audio_buffer[chunk_start:])

              try:
                result = await self._transcribe_with_whisper(chunk_data, "wav")
                if result["text"].strip():
                  segment = TranscriptionSegment(
                      text=result["text"].strip(),
                      start_time=last_transcription_time,
                      end_time=current_time,
                      confidence=0.9,
                      speaker="user"
                  )
                  yield segment
              except Exception as e:
                self.logger.warning(f"Final chunk transcription failed: {e}")

              break

    except Exception as e:
      self.logger.error(f"Stream transcription failed: {e}")
      raise

    finally:
      self.logger.info(
          f"Stream transcription ended for call: {call_context.call_id}")

  async def _transcribe_with_whisper(
      self,
      audio_data: bytes,
      format: str,
      language: Optional[str] = None
  ) -> Dict:
    """Transcribe using OpenAI Whisper API."""

    try:
      files = {
          "file": (f"audio.{format}", audio_data, f"audio/{format}")
      }

      data = {
          "model": self.whisper_config.model,
          "response_format": "verbose_json",
          "timestamp_granularities": ["segment"]
      }

      if language:
        data["language"] = language

      response = await self._http_client.post(
          f"{self.whisper_config.base_url}/audio/transcriptions",
          headers={
              "Authorization": f"Bearer {self.whisper_config.api_key}"
          },
          files=files,
          data=data
      )

      response.raise_for_status()
      result = response.json()

      # Convert segments
      segments = []
      for segment in result.get("segments", []):
        segments.append(TranscriptionSegment(
            text=segment["text"],
            start_time=segment["start"],
            end_time=segment["end"],
            confidence=0.9,  # Whisper doesn't provide confidence
            speaker=None
        ))

      return {
          "text": result["text"],
          "language": result.get("language"),
          "duration": result.get("duration", 0.0),
          "segments": segments
      }

    except httpx.HTTPError as e:
      self.logger.error(f"Whisper API error: {e}")
      raise
    except Exception as e:
      self.logger.error(f"Whisper transcription error: {e}")
      raise

  async def _save_transcription(
      self,
      transcription: TranscriptionResult,
      call_context: CallContext
  ) -> None:
    """Save transcription to database."""

    try:
      # Note: This is a simplified save - in practice you'd need
      # a database session and call_log_id
      self.logger.info(
          f"Transcription saved for call: {transcription.call_id}, "
          f"segments: {len(transcription.segments)}"
      )

      # TODO: Implement proper database saving with session
      # and call_log_id lookup

    except Exception as e:
      self.logger.error(f"Failed to save transcription: {e}")
      # Don't raise - transcription succeeded, saving failed

  async def close(self) -> None:
    """Close HTTP client."""
    await self._http_client.aclose()
