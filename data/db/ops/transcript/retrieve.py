"""
Retrieve operations for transcripts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from ...models.transcript import Transcript
from ....core.logging import get_logger

logger = get_logger(__name__)


async def get_call_transcripts(
    session: AsyncSession,
    call_log_id: int
) -> List[Transcript]:
    """
    Get all transcripts for a call.
    
    Args:
        session: Database session
        call_log_id: Call log ID
        
    Returns:
        List of Transcript instances ordered by timestamp
    """
    try:
        result = await session.execute(
            select(Transcript)
            .where(Transcript.call_log_id == call_log_id)
            .order_by(Transcript.timestamp)
        )
        return result.scalars().all()
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to get transcripts for call {call_log_id}: {e}")
        return []


async def get_transcript_by_segment(
    session: AsyncSession,
    segment_id: str
) -> Optional[Transcript]:
    """
    Get transcript by segment ID.
    
    Args:
        session: Database session
        segment_id: Segment identifier
        
    Returns:
        Transcript instance or None if not found
    """
    try:
        result = await session.execute(
            select(Transcript).where(Transcript.segment_id == segment_id)
        )
        return result.scalar_one_or_none()
        
    except SQLAlchemyError as e:
        logger.error(f"Failed to get transcript segment {segment_id}: {e}")
        return None
