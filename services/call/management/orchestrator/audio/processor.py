"""
Audio processing module for orchestrator.
Handles audio stream processing logic separate from task execution.
"""
import asyncio
import json
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from core.startup.services.access import get_stt_service, get_tts_service, get_llm_service
from models.external.llm.request import LLMRequest, LLMMessage

logger = get_logger(__name__)


class AudioProcessor:
  """
  Handles audio processing logic for calls.
  Manages STT, LLM, and TTS pipeline coordination using services from startup context.
  """

  def __init__(self, startup_context: Any):
    """
    Initialize the audio processor with startup context.

    Args:
        startup_context: Application startup context containing initialized services
    """
    self.startup_context = startup_context
    self.active_processors: Dict[str, Dict[str, Any]] = {}

    # Services will be retrieved from context when needed
    self._stt_service = None
    self._llm_service = None
    self._tts_service = None

    logger.info("Audio processor initialized with startup context")

  async def _get_services(self):
    """Get services from startup context if not already retrieved."""
    if self._stt_service is None:
      self._stt_service = await get_stt_service(self.startup_context)
      if self._stt_service:
        logger.info("✅ STT service retrieved from startup context")
      else:
        logger.error("❌ Failed to retrieve STT service from startup context")

    if self._llm_service is None:
      self._llm_service = await get_llm_service(self.startup_context)
      if self._llm_service:
        logger.info("✅ LLM service retrieved from startup context")
      else:
        logger.error("❌ Failed to retrieve LLM service from startup context")

    if self._tts_service is None:
      self._tts_service = await get_tts_service(self.startup_context)
      if self._tts_service:
        logger.info("✅ TTS service retrieved from startup context")
      else:
        logger.error("❌ Failed to retrieve TTS service from startup context")

  async def process_audio_chunk(self, call_id: str, audio_data: Dict[str, Any], agent_id: str) -> Optional[str]:
    """
    Process an audio chunk through the STT->LLM->TTS pipeline.

    Args:
        call_id: Ringover call ID
        audio_data: Raw audio data from ringover-streamer
        agent_id: Agent handling the call

    Returns:
        Generated response audio URL or None
    """
    try:
      logger.debug(f"🎙️ Processing audio chunk for call {call_id}")

      # Ensure services are available
      await self._get_services()

      # Check if all required services are available
      if not self._stt_service or not self._llm_service or not self._tts_service:
        logger.error(f"❌ Required services not available for call {call_id}")
        return None

      # 1. Extract audio from data
      raw_audio = audio_data.get("audio_data")
      if not raw_audio:
        logger.warning(f"No audio data found in chunk for call {call_id}")
        return None

      # 2. Process through STT (Speech-to-Text)
      transcription = await self._process_stt(raw_audio, call_id)
      if not transcription:
        return None

      # 3. Process through LLM for response generation
      response_text = await self._process_llm(transcription, call_id, agent_id)
      if not response_text:
        return None

      # 4. Process through TTS (Text-to-Speech)
      response_audio_url = await self._process_tts(response_text, call_id)

      return response_audio_url

    except Exception as e:
      logger.error(f"Failed to process audio chunk for call {call_id}: {e}")
      return None

  async def _process_stt(self, raw_audio: bytes, call_id: str) -> Optional[str]:
    """
    Process raw audio through Speech-to-Text.

    Args:
        raw_audio: Raw audio bytes
        call_id: Call ID for context

    Returns:
        Transcribed text or None
    """
    try:
      if not self._stt_service:
        logger.error(f"STT service not available for call {call_id}")
        return None

      # Process audio through STT service
      transcription = await self._stt_service.transcribe_audio(raw_audio)

      if transcription:
        logger.debug(f"🗣️ STT result for call {call_id}: {transcription}")
        return transcription
      else:
        logger.warning(f"No transcription result for call {call_id}")
        return None

    except Exception as e:
      logger.error(f"STT processing failed for call {call_id}: {e}")
      return None

  async def _process_llm(self, transcription: str, call_id: str, agent_id: str) -> Optional[str]:
    """
    Process transcription through LLM for response generation.

    Args:
        transcription: Input text from STT
        call_id: Call ID for context
        agent_id: Agent handling the call

    Returns:
        Generated response text or None
    """
    try:
      if not self._llm_service:
        logger.error(f"LLM service not available for call {call_id}")
        return None

      # Create LLM request
      messages = [
          LLMMessage(
              role="system", content="You are a helpful customer service assistant."),
          LLMMessage(role="user", content=transcription)
      ]

      # Generate response using LLM orchestrator
      response = await self._llm_service.generate_response(
          messages=[msg.dict() for msg in messages],
          provider="openai",
          max_tokens=150
      )

      if response and response.choices:
        response_text = response.choices[0].message.content.strip()
        logger.debug(f"🤖 LLM response for call {call_id}: {response_text}")
        return response_text
      else:
        logger.warning(f"No LLM response generated for call {call_id}")
        return None

    except Exception as e:
      logger.error(f"LLM processing failed for call {call_id}: {e}")
      return None

  async def _process_tts(self, response_text: str, call_id: str) -> Optional[str]:
    """
    Process response text through Text-to-Speech.

    Args:
        response_text: Text to convert to speech
        call_id: Call ID for context

    Returns:
        Audio file URL or None
    """
    try:
      if not self._tts_service:
        logger.error(f"TTS service not available for call {call_id}")
        return None

      # Generate audio using TTS service
      audio_response = await self._tts_service.generate_speech(response_text)

      if audio_response and hasattr(audio_response, 'audio_url'):
        audio_url = audio_response.audio_url
        logger.debug(f"🎵 TTS result for call {call_id}: {audio_url}")
        return audio_url
      elif audio_response and hasattr(audio_response, 'content'):
        # Handle case where audio data is returned directly
        # TODO: Save to file or stream and return URL
        logger.debug(f"🎵 TTS audio data generated for call {call_id}")
        # For now, return a placeholder indicating audio was generated
        return "audio_data_generated"
      else:
        logger.warning(f"No TTS audio generated for call {call_id}")
        return None

    except Exception as e:
      logger.error(f"TTS processing failed for call {call_id}: {e}")
      return None

  def initialize_processor(self, call_id: str, session_id: str, agent_id: str) -> None:
    """
    Initialize audio processor for a specific call.

    Args:
        call_id: Ringover call ID
        session_id: Internal session ID
        agent_id: Agent handling the call
    """
    self.active_processors[call_id] = {
        "session_id": session_id,
        "agent_id": agent_id,
        "conversation_history": [],
        "initialized_at": asyncio.get_event_loop().time()
    }
    logger.info(f"🎧 Audio processor initialized for call {call_id}")

  def cleanup_processor(self, call_id: str) -> None:
    """
    Clean up audio processor for a call.

    Args:
        call_id: Ringover call ID
    """
    if call_id in self.active_processors:
      del self.active_processors[call_id]
      logger.info(f"🧹 Audio processor cleaned up for call {call_id}")

  def get_processor_status(self, call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get the status of an audio processor.

    Args:
        call_id: Ringover call ID

    Returns:
        Processor status or None if not found
    """
    return self.active_processors.get(call_id)
