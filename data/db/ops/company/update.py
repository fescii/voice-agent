"""
Update operations for companies.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime, timezone

from data.db.models.company import Company
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def update_company(
    session: AsyncSession,
    company_id: str,
    **kwargs
) -> Optional[Company]:
  """
  Update company information.

  Args:
      session: Database session
      company_id: Company ID
      **kwargs: Fields to update

  Returns:
      Updated Company object or None if failed
  """
  try:
    # Add updated timestamp
    kwargs["updated_at"] = datetime.now(timezone.utc)

    stmt = update(Company).where(Company.id == company_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()

    # Get updated company
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    updated_company = result.scalar_one_or_none()

    if updated_company:
      logger.info(f"Updated company: {company_id}")
      return updated_company
    else:
      logger.warning(f"Company not found for update: {company_id}")
      return None

  except SQLAlchemyError as e:
    logger.error(f"Failed to update company {company_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error updating company {company_id}: {e}")
    await session.rollback()
    return None
