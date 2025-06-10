"""
Read operations for deals.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from data.db.models.deal import Deal
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_deal(
    session: AsyncSession,
    deal_id: str
) -> Optional[Deal]:
  """
  Get deal by ID.

  Args:
      session: Database session
      deal_id: Deal ID

  Returns:
      Deal object or None if not found
  """
  try:
    stmt = select(Deal).where(Deal.id == deal_id)
    result = await session.execute(stmt)
    deal = result.scalar_one_or_none()

    if deal:
      logger.debug(f"Found deal: {deal_id}")
    else:
      logger.debug(f"Deal not found: {deal_id}")

    return deal

  except SQLAlchemyError as e:
    logger.error(f"Failed to get deal {deal_id}: {e}")
    return None


async def get_deals_by_contact(
    session: AsyncSession,
    contact_id: str
) -> List[Deal]:
  """
  Get deals by contact ID.

  Args:
      session: Database session
      contact_id: Contact ID

  Returns:
      List of Deal objects
  """
  try:
    stmt = select(Deal).where(Deal.contact_id == contact_id)
    result = await session.execute(stmt)
    deals = result.scalars().all()

    logger.debug(f"Found {len(deals)} deals for contact: {contact_id}")
    return list(deals)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get deals by contact {contact_id}: {e}")
    return []


async def get_deals_by_company(
    session: AsyncSession,
    company_id: str
) -> List[Deal]:
  """
  Get deals by company ID.

  Args:
      session: Database session
      company_id: Company ID

  Returns:
      List of Deal objects
  """
  try:
    stmt = select(Deal).where(Deal.company_id == company_id)
    result = await session.execute(stmt)
    deals = result.scalars().all()

    logger.debug(f"Found {len(deals)} deals for company: {company_id}")
    return list(deals)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get deals by company {company_id}: {e}")
    return []
