"""
Delete operations for contacts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from data.db.models.contact import Contact
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def delete_contact(
    session: AsyncSession,
    contact_id: str
) -> bool:
  """
  Delete contact by ID.

  Args:
      session: Database session
      contact_id: Contact ID

  Returns:
      True if deleted successfully, False otherwise
  """
  try:
    # Check if contact exists first
    stmt = select(Contact).where(Contact.id == contact_id)
    result = await session.execute(stmt)
    contact = result.scalar_one_or_none()

    if not contact:
      logger.warning(f"Contact not found for deletion: {contact_id}")
      return False

    # Delete the contact
    stmt = delete(Contact).where(Contact.id == contact_id)
    await session.execute(stmt)
    await session.commit()

    logger.info(f"Deleted contact: {contact_id}")
    return True

  except SQLAlchemyError as e:
    logger.error(f"Failed to delete contact {contact_id}: {e}")
    await session.rollback()
    return False
  except Exception as e:
    logger.error(f"Unexpected error deleting contact {contact_id}: {e}")
    await session.rollback()
    return False
