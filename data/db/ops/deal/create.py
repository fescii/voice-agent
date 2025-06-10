"""
Create operations for deals.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional

from data.db.models.deal import Deal, DealStage, DealType
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def create_deal(
    session: AsyncSession,
    name: str,
    contact_id: str,
    company_id: str,
    owner_id: str,
    **kwargs
) -> Optional[Deal]:
  """
  Create a new deal record.

  Args:
      session: Database session
      name: Deal name (required)
      contact_id: Associated contact ID (required)
      company_id: Associated company ID (required)
      owner_id: Sales rep/owner ID (required)
      **kwargs: Additional deal fields

  Returns:
      Created Deal object or None if failed
  """
  try:
    deal = Deal(
        name=name,
        contact_id=contact_id,
        company_id=company_id,
        owner_id=owner_id,
        **kwargs
    )

    session.add(deal)
    await session.commit()
    await session.refresh(deal)

    logger.info(f"Created deal: {deal.id} - {name}")
    return deal

  except SQLAlchemyError as e:
    logger.error(f"Failed to create deal {name}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error creating deal {name}: {e}")
    await session.rollback()
    return None
