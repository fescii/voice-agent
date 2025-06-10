"""
Read operations for companies.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from data.db.models.company import Company
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_company(
    session: AsyncSession,
    company_id: str
) -> Optional[Company]:
  """
  Get company by ID.

  Args:
      session: Database session
      company_id: Company ID

  Returns:
      Company object or None if not found
  """
  try:
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()

    if company:
      logger.debug(f"Found company: {company_id}")
    else:
      logger.debug(f"Company not found: {company_id}")

    return company

  except SQLAlchemyError as e:
    logger.error(f"Failed to get company {company_id}: {e}")
    return None


async def get_companies_by_domain(
    session: AsyncSession,
    domain: str
) -> List[Company]:
  """
  Get companies by domain.

  Args:
      session: Database session
      domain: Domain to search for

  Returns:
      List of Company objects
  """
  try:
    stmt = select(Company).where(Company.domain == domain)
    result = await session.execute(stmt)
    companies = result.scalars().all()

    logger.debug(f"Found {len(companies)} companies for domain: {domain}")
    return list(companies)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get companies by domain {domain}: {e}")
    return []


async def get_company_by_name(
    session: AsyncSession,
    name: str
) -> Optional[Company]:
  """
  Get company by name.

  Args:
      session: Database session
      name: Company name

  Returns:
      Company object or None if not found
  """
  try:
    stmt = select(Company).where(Company.name == name)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()

    if company:
      logger.debug(f"Found company by name: {name}")
    else:
      logger.debug(f"Company not found by name: {name}")

    return company

  except SQLAlchemyError as e:
    logger.error(f"Failed to get company by name {name}: {e}")
    return None
