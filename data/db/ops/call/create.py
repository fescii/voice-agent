"""
Create operations for call logs.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime

from ...models.calllog import CallLog, CallStatus, CallDirection
from ....core.logging import get_logger

logger = get_logger(__name__)


async def create_call_log(
    session: AsyncSession,
    call_id: str,
    agent_id: str,
    caller_number: str,
    callee_number: str,
    direction: CallDirection,
    ringover_call_id: Optional[str] = None,
    **kwargs
) -> Optional[CallLog]:
  """
  Create a new call log entry.

  Args:
      session: Database session
      call_id: Unique call identifier
      agent_id: Agent handling the call
      caller_number: Caller phone number
      callee_number: Callee phone number
      direction: Call direction (inbound/outbound)
      ringover_call_id: Ringover's call identifier
      **kwargs: Additional call metadata

  Returns:
      Created CallLog instance or None if failed
  """
  try:
    call_log = CallLog(
        call_id=call_id,
        ringover_call_id=ringover_call_id,
        agent_id=agent_id,
        caller_number=caller_number,
        callee_number=callee_number,
        direction=direction,
        status=CallStatus.INITIATED,
        initiated_at=datetime.utcnow(),
        **kwargs
    )

    session.add(call_log)
    await session.commit()
    await session.refresh(call_log)

    logger.info(f"Created call log: {call_id}")
    return call_log

  except SQLAlchemyError as e:
    logger.error(f"Failed to create call log {call_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error creating call log {call_id}: {e}")
    await session.rollback()
    return None
