"""
Create operations for contacts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from data.db.models.contact import Contact, ContactType, LeadStatus
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def create_contact(
    session: AsyncSession,
    phone_primary: str,
    contact_type: ContactType = ContactType.LEAD,
    **kwargs
) -> Optional[Contact]:
  """
  Create a new contact record.

  Args:
      session: Database session
      phone_primary: Primary phone number (required)
      contact_type: Type of contact
      **kwargs: Additional contact fields

  Returns:
      Created Contact object or None if failed
  """
  try:
    # Generate full_name if not provided but first/last names are
    if "full_name" not in kwargs and "first_name" in kwargs:
      first_name = kwargs.get("first_name", "")
      last_name = kwargs.get("last_name", "")
      kwargs["full_name"] = f"{first_name} {last_name}".strip()

    contact = Contact(
        phone_primary=phone_primary,
        contact_type=contact_type,
        **kwargs
    )

    session.add(contact)
    await session.commit()
    await session.refresh(contact)

    logger.info(
        f"Created contact: {contact.id} ({contact.full_name or 'No name'}) - {phone_primary}")
    return contact

  except SQLAlchemyError as e:
    logger.error(f"Failed to create contact {phone_primary}: {e}")
    await session.rollback()
    return None
  except Exception as e:
    logger.error(f"Unexpected error creating contact {phone_primary}: {e}")
    await session.rollback()
    return None
