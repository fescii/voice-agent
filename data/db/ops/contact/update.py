"""
Update operations for contacts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from data.db.models.contact import Contact
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def update_contact(
    session: AsyncSession,
    contact_id: str,
    **kwargs
) -> Optional[Contact]:
  """
  Update contact information.

  Args:
      session: Database session
      contact_id: Contact ID
      **kwargs: Fields to update

  Returns:
      Updated Contact object or None if failed
  """
  try:
    # Update full_name if first_name or last_name changed
    if "first_name" in kwargs or "last_name" in kwargs:
      # Get current contact to merge names
      stmt = select(Contact).where(Contact.id == contact_id)
      result = await session.execute(stmt)
      current_contact = result.scalar_one_or_none()

      if current_contact:
        first_name = kwargs.get("first_name", current_contact.first_name or "")
        last_name = kwargs.get("last_name", current_contact.last_name or "")
        kwargs["full_name"] = f"{first_name} {last_name}".strip()

    # Add updated timestamp
    kwargs["updated_at"] = datetime.now(timezone.utc)

    stmt = update(Contact).where(Contact.id == contact_id).values(**kwargs)
    await session.execute(stmt)
    await session.commit()

    # Get updated contact
    stmt = select(Contact).where(Contact.id == contact_id)
    result = await session.execute(stmt)
    updated_contact = result.scalar_one_or_none()

    if updated_contact:
      logger.info(f"Updated contact: {contact_id}")
      return updated_contact
    else:
      logger.warning(f"Contact not found for update: {contact_id}")
      return None

  except SQLAlchemyError as e:
    logger.error(f"Failed to update contact {contact_id}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error updating contact {contact_id}: {e}")
    await session.rollback()
    return None
