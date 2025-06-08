"""Real-time transcription service for live audio streams."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Optional, Set

from pydantic import BaseModel

from core.logging.setup import get_logger
from .processor import TranscriptionProcessor, TranscriptionSegment
from models.internal.callcontext import CallContext


class RealtimeTranscriptionSession(BaseModel):
  """Real-time transcription session model."""

  call_id: str
  session_id: str
  started_at: datetime
  language: Optional[str] = None
  is_active: bool = True


class RealtimeTranscription:
  """Manages real-time transcription sessions."""

  def __init__(self, transcription_processor: TranscriptionProcessor):
    self.logger = get_logger(__name__)
    self.processor = transcription_processor
    self._active_sessions: Dict[str, RealtimeTranscriptionSession] = {}
    self._audio_queues: Dict[str, asyncio.Queue] = {}
    self._transcription_tasks: Dict[str, asyncio.Task] = {}
    self._subscribers: Dict[str, Set[asyncio.Queue]] = {}

  async def start_session(
      self,
      call_context: CallContext,
      language: Optional[str] = None
  ) -> str:
    """Start a real-time transcription session."""

    session_id = f"rt_{call_context.call_id}_{datetime.now(timezone.utc).timestamp()}"

    self.logger.info(f"Starting real-time transcription session: {session_id}")

    # Create session
    session = RealtimeTranscriptionSession(
        call_id=call_context.call_id,
        session_id=session_id,
        started_at=datetime.now(timezone.utc),
        language=language
    )

    self._active_sessions[session_id] = session
    self._audio_queues[session_id] = asyncio.Queue()
    self._subscribers[session_id] = set()

    # Start transcription task
    self._transcription_tasks[session_id] = asyncio.create_task(
        self._transcription_loop(session_id, call_context)
    )

    return session_id

  async def stop_session(self, session_id: str) -> None:
    """Stop a real-time transcription session."""

    if session_id not in self._active_sessions:
      return

    self.logger.info(f"Stopping real-time transcription session: {session_id}")

    # Mark session as inactive
    session = self._active_sessions[session_id]
    session.is_active = False

    # Signal end of audio stream
    audio_queue = self._audio_queues.get(session_id)
    if audio_queue:
      await audio_queue.put(None)  # End of stream marker

    # Wait for transcription task to complete
    task = self._transcription_tasks.get(session_id)
    if task and not task.done():
      try:
        await asyncio.wait_for(task, timeout=5.0)
      except asyncio.TimeoutError:
        task.cancel()
        self.logger.warning(f"Transcription task for {session_id} timed out")

    # Clean up
    self._active_sessions.pop(session_id, None)
    self._audio_queues.pop(session_id, None)
    self._transcription_tasks.pop(session_id, None)
    self._subscribers.pop(session_id, None)

  async def add_audio_chunk(self, session_id: str, audio_data: bytes) -> None:
    """Add audio chunk to transcription queue."""

    if session_id not in self._active_sessions:
      raise ValueError(f"Session {session_id} not found")

    if not self._active_sessions[session_id].is_active:
      raise ValueError(f"Session {session_id} is not active")

    audio_queue = self._audio_queues[session_id]
    await audio_queue.put(audio_data)

  async def subscribe_to_transcription(
      self,
      session_id: str
  ) -> asyncio.Queue:
    """Subscribe to transcription results for a session."""

    if session_id not in self._active_sessions:
      raise ValueError(f"Session {session_id} not found")

    result_queue = asyncio.Queue()
    self._subscribers[session_id].add(result_queue)

    return result_queue

  async def unsubscribe_from_transcription(
      self,
      session_id: str,
      result_queue: asyncio.Queue
  ) -> None:
    """Unsubscribe from transcription results."""

    if session_id in self._subscribers:
      self._subscribers[session_id].discard(result_queue)

  async def get_session_info(self, session_id: str) -> Optional[RealtimeTranscriptionSession]:
    """Get session information."""
    return self._active_sessions.get(session_id)

  async def get_active_sessions(self) -> Dict[str, RealtimeTranscriptionSession]:
    """Get all active sessions."""
    return {
        sid: session
        for sid, session in self._active_sessions.items()
        if session.is_active
    }

  async def _transcription_loop(
      self,
      session_id: str,
      call_context: CallContext
  ) -> None:
    """Main transcription loop for a session."""

    try:
      self.logger.info(
          f"Starting transcription loop for session: {session_id}")

      audio_queue = self._audio_queues[session_id]

      # Start stream transcription
      async for segment in self.processor.transcribe_stream(
          audio_queue, call_context
      ):
        # Broadcast to subscribers
        await self._broadcast_segment(session_id, segment)

        self.logger.debug(
            f"Transcribed segment for {session_id}: "
            f"{segment.text[:50]}{'...' if len(segment.text) > 50 else ''}"
        )

    except Exception as e:
      self.logger.error(f"Transcription loop error for {session_id}: {e}")

    finally:
      self.logger.info(f"Transcription loop ended for session: {session_id}")

  async def _broadcast_segment(
      self,
      session_id: str,
      segment: TranscriptionSegment
  ) -> None:
    """Broadcast transcription segment to all subscribers."""

    subscribers = self._subscribers.get(session_id, set())

    for result_queue in subscribers.copy():  # Copy to avoid modification during iteration
      try:
        await result_queue.put(segment)
      except Exception as e:
        self.logger.warning(f"Failed to send segment to subscriber: {e}")
        # Remove failed subscriber
        subscribers.discard(result_queue)

  async def get_session_statistics(self, session_id: str) -> Optional[Dict]:
    """Get statistics for a session."""

    session = self._active_sessions.get(session_id)
    if not session:
      return None

    audio_queue = self._audio_queues.get(session_id)
    subscribers = self._subscribers.get(session_id, set())

    stats = {
        "session_id": session_id,
        "call_id": session.call_id,
        "started_at": session.started_at,
        "is_active": session.is_active,
        "language": session.language,
        "audio_queue_size": audio_queue.qsize() if audio_queue else 0,
        "subscriber_count": len(subscribers),
        "uptime_seconds": (datetime.now(timezone.utc) - session.started_at).total_seconds()
    }

    return stats

  async def cleanup_inactive_sessions(self) -> None:
    """Clean up inactive sessions."""

    inactive_sessions = [
        sid for sid, session in self._active_sessions.items()
        if not session.is_active
    ]

    for session_id in inactive_sessions:
      await self.stop_session(session_id)

    if inactive_sessions:
      self.logger.info(
          f"Cleaned up {len(inactive_sessions)} inactive sessions")
