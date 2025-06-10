"""
Create operations for companies.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional
from datetime import datetime, timezone

from data.db.models.company import Company, CompanyType
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def create_company(
    session: AsyncSession,
    name: str,
    company_type: CompanyType = CompanyType.PROSPECT,
    **kwargs
) -> Optional[Company]:
  """
  Create a new company record.

  Args:
      session: Database session
      name: Company name (required)
      company_type: Type of company
      **kwargs: Additional company fields

  Returns:
      Created Company object or None if failed
  """
  try:
    company = Company(
        name=name,
        company_type=company_type,
        **kwargs
    )

    session.add(company)
    await session.commit()
    await session.refresh(company)

    logger.info(f"Created company: {company.id} - {name}")
    return company

  except SQLAlchemyError as e:
    logger.error(f"Failed to create company {name}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error creating company {name}: {e}")
    await session.rollback()
    return None
