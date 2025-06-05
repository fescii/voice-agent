"""
Handler for Ringover streaming audio and transcription.
"""
import asyncio
from typing import Dict, Any, Optional, Callable, Awaitable, List
import json
import uuid
from datetime import datetime

from core.logging.setup import get_logger
from services.stt.whisper import WhisperService
from services.llm.prompt.builder import PromptBuilder, ConversationContext

logger = get_logger(__name__)


class RingoverStreamHandler:
  """
  Handles real-time audio streams from Ringover.

  This class processes incoming RTP streams from Ringover,
  passes them to a transcription service, and forwards the
  transcriptions to the LLM for real-time response generation.
  """

  def __init__(
      self,
      transcriber: WhisperService,
      prompt_builder: PromptBuilder,
      callback: Optional[Callable[[
          str, Dict[str, Any]], Awaitable[None]]] = None
  ):
    """
    Initialize the stream handler.

    Args:
        transcriber: The STT service to use for transcription
        prompt_builder: The prompt builder for LLM context management
        callback: Optional callback for transcription segments
    """
    self.transcriber = transcriber
    self.prompt_builder = prompt_builder
    self.callback = callback
    self.current_audio_buffer = bytearray()
    self.conversation_context = None
    self.current_prompt = None
    self.last_transcription_time = None
    self.session_id = str(uuid.uuid4())
    self.transcription_buffer = []

  async def handle_audio_chunk(self, audio_data: bytes, metadata: Dict[str, Any]):
    """
    Process an incoming chunk of audio.

    Args:
        audio_data: The raw audio data
        metadata: Metadata about the audio
    """
    try:
      # Add to buffer
      self.current_audio_buffer.extend(audio_data)

      current_time = datetime.now()

      # Process if buffer is large enough or enough time has passed
      buffer_size = len(self.current_audio_buffer)
      time_condition = (self.last_transcription_time is None or
                        (current_time - self.last_transcription_time).total_seconds() >= 0.5)

      if buffer_size >= 4000 or (buffer_size > 0 and time_condition):
        # Process the accumulated audio
        await self._process_audio_buffer(metadata)
        self.last_transcription_time = current_time

    except Exception as e:
      logger.error(f"Error processing audio chunk: {e}")

  async def _process_audio_buffer(self, metadata: Dict[str, Any]):
    """
    Process the current audio buffer.

    Args:
        metadata: Metadata about the audio
    """
    if not self.current_audio_buffer:
      return

    # Get audio to process
    audio_data = bytes(self.current_audio_buffer)
    self.current_audio_buffer = bytearray()

    # Get transcription
    transcription_result = await self.transcriber.transcribe_audio(
        audio_data, metadata.get("language", "en")
    )

    if not transcription_result or not transcription_result.get("text"):
      return

    text = transcription_result["text"].strip()
    if not text:
      return

    # Add to transcription buffer
    self.transcription_buffer.append(text)

    # Update context and prompt if available
    if self.conversation_context and self.current_prompt:
      updated_prompt = self.prompt_builder.update_with_streaming_transcription(
          self.current_prompt,
          " ".join(self.transcription_buffer)
      )
      self.current_prompt = updated_prompt

    # Call the callback if provided
    if self.callback:
      await self.callback(text, {
          "session_id": self.session_id,
          "timestamp": datetime.now().isoformat(),
          "interim": True,
          **metadata
      })

  async def start_session(self, call_id: str, caller_info: Dict[str, Any], context: Optional[Dict[str, Any]] = None):
    """
    Start a new streaming session.

    Args:
        call_id: The ID of the call
        caller_info: Information about the caller
        context: Additional context information
    """
    logger.info(f"Starting new streaming session for call {call_id}")
    self.session_id = str(uuid.uuid4())
    self.conversation_context = ConversationContext(
        call_id=call_id,
        caller_info=caller_info,
        conversation_history=[],
        metadata=context
    )
    self.current_audio_buffer = bytearray()
    self.transcription_buffer = []
    self.last_transcription_time = None

  async def end_utterance(self) -> Optional[str]:
    """
    End the current utterance and get the complete transcription.

    Returns:
        The complete transcription of the utterance
    """
    # Process any remaining audio first
    if self.current_audio_buffer:
      await self._process_audio_buffer({})

    # Get the complete transcription
    complete_transcription = " ".join(self.transcription_buffer).strip()

    # Reset buffers
    self.current_audio_buffer = bytearray()
    self.transcription_buffer = []

    # Call the callback with final transcription
    if self.callback and complete_transcription:
      await self.callback(complete_transcription, {
          "session_id": self.session_id,
          "timestamp": datetime.now().isoformat(),
          "interim": False
      })

    return complete_transcription if complete_transcription else None

  async def end_session(self):
    """End the current streaming session."""
    logger.info(f"Ending streaming session {self.session_id}")

    # Process any remaining audio and get final transcription
    final_transcription = await self.end_utterance()

    # Reset context
    self.conversation_context = None
    self.current_prompt = None

    return final_transcription
