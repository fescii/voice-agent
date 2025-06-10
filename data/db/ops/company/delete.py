"""
Delete operations for companies.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from data.db.models.company import Company
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def delete_company(
    session: AsyncSession,
    company_id: str
) -> bool:
  """
  Delete company by ID.

  Args:
      session: Database session
      company_id: Company ID

  Returns:
      True if deleted successfully, False otherwise
  """
  try:
    # Check if company exists first
    stmt = select(Company).where(Company.id == company_id)
    result = await session.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
      logger.warning(f"Company not found for deletion: {company_id}")
      return False

    # Delete the company
    stmt = delete(Company).where(Company.id == company_id)
    await session.execute(stmt)
    await session.commit()

    logger.info(f"Deleted company: {company_id}")
    return True

  except SQLAlchemyError as e:
    logger.error(f"Failed to delete company {company_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error deleting company {company_id}: {e}")
    await session.rollback()
    return False
