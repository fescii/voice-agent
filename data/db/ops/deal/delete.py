"""
Delete operations for deals.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from data.db.models.deal import Deal
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def delete_deal(
    session: AsyncSession,
    deal_id: str
) -> bool:
  """
  Delete deal by ID.

  Args:
      session: Database session
      deal_id: Deal ID

  Returns:
      True if deleted successfully, False otherwise
  """
  try:
    # Check if deal exists first
    stmt = select(Deal).where(Deal.id == deal_id)
    result = await session.execute(stmt)
    deal = result.scalar_one_or_none()

    if not deal:
      logger.warning(f"Deal not found for deletion: {deal_id}")
      return False

    # Delete the deal
    stmt = delete(Deal).where(Deal.id == deal_id)
    await session.execute(stmt)
    await session.commit()

    logger.info(f"Deleted deal: {deal_id}")
    return True

  except SQLAlchemyError as e:
    logger.error(f"Failed to delete deal {deal_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error deleting deal {deal_id}: {e}")
    await session.rollback()
    return False
