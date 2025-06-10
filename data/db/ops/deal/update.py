"""
Update operations for deals.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime, timezone

from data.db.models.deal import Deal, DealStage
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def update_deal(
    session: AsyncSession,
    deal_id: str,
    **kwargs
) -> Optional[Deal]:
  """
  Update deal information.

  Args:
      session: Database session
      deal_id: Deal ID
      **kwargs: Fields to update

  Returns:
      Updated Deal object or None if failed
  """
  try:
    # Add updated timestamp
    kwargs["updated_at"] = datetime.now(timezone.utc)

    stmt = update(Deal).where(Deal.id == deal_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()

    # Get updated deal
    stmt = select(Deal).where(Deal.id == deal_id)
    result = await session.execute(stmt)
    updated_deal = result.scalar_one_or_none()

    if updated_deal:
      logger.info(f"Updated deal: {deal_id}")
      return updated_deal
    else:
      logger.warning(f"Deal not found for update: {deal_id}")
      return None

  except SQLAlchemyError as e:
    logger.error(f"Failed to update deal {deal_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error updating deal {deal_id}: {e}")
    await session.rollback()
    return None


async def update_deal_stage(
    session: AsyncSession,
    deal_id: str,
    stage: DealStage,
    **kwargs
) -> Optional[Deal]:
  """
  Update deal stage and related fields.

  Args:
      session: Database session
      deal_id: Deal ID
      stage: New deal stage
      **kwargs: Additional fields to update

  Returns:
      Updated Deal object or None if failed
  """
  try:
    update_data = {"stage": stage, **kwargs}

    # Set close date if deal is won or lost
    if stage in [DealStage.CLOSED_WON, DealStage.CLOSED_LOST]:
      update_data["actual_close_date"] = datetime.now(timezone.utc)
      update_data["is_won"] = (stage == DealStage.CLOSED_WON)
      update_data["is_lost"] = (stage == DealStage.CLOSED_LOST)

    return await update_deal(session, deal_id, **update_data)

  except Exception as e:
    logger.error(f"Unexpected error updating deal stage {deal_id}: {e}")
    return None
