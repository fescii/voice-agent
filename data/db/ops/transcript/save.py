"""
Save operations for transcripts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime

from ...models.transcript import Transcript
from ....core.logging import get_logger

logger = get_logger(__name__)


async def save_transcript(
    session: AsyncSession,
    call_log_id: int,
    speaker: str,
    text: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    confidence_score: Optional[float] = None,
    segment_id: Optional[str] = None,
    **kwargs
) -> Optional[Transcript]:
  """
  Save a transcript segment.

  Args:
      session: Database session
      call_log_id: Associated call log ID
      speaker: Speaker identifier (caller, agent, system)
      text: Transcribed text
      start_time: Start time in seconds from call start
      end_time: End time in seconds from call start
      confidence_score: STT confidence score
      segment_id: Unique segment identifier
      **kwargs: Additional metadata

  Returns:
      Created Transcript instance or None if failed
  """
  try:
    transcript = Transcript(
        call_log_id=call_log_id,
        speaker=speaker,
        text=text,
        start_time=start_time,
        end_time=end_time,
        confidence_score=confidence_score,
        segment_id=segment_id,
        timestamp=datetime.utcnow(),
        **kwargs
    )

    session.add(transcript)
    await session.commit()
    await session.refresh(transcript)

    logger.debug(f"Saved transcript segment for call {call_log_id}")
    return transcript

  except SQLAlchemyError as e:
    logger.error(f"Failed to save transcript for call {call_log_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(
        f"Unexpected error saving transcript for call {call_log_id}: {e}")
    await session.rollback()
    return None
