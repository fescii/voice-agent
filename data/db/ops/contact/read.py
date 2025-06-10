"""
Read operations for contacts.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from data.db.models.contact import Contact
from core.logging.setup import get_logger

logger = get_logger(__name__)


async def get_contact(
    session: AsyncSession,
    contact_id: str
) -> Optional[Contact]:
  """
  Get contact by ID.

  Args:
      session: Database session
      contact_id: Contact ID

  Returns:
      Contact object or None if not found
  """
  try:
    stmt = select(Contact).where(Contact.id == contact_id)
    result = await session.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
      logger.debug(f"Found contact: {contact_id}")
    else:
      logger.debug(f"Contact not found: {contact_id}")

    return contact

  except SQLAlchemyError as e:
    logger.error(f"Failed to get contact {contact_id}: {e}")
    return None


async def get_contacts_by_phone(
    session: AsyncSession,
    phone_number: str
) -> List[Contact]:
  """
  Get contacts by phone number (primary or secondary).

  Args:
      session: Database session
      phone_number: Phone number to search for

  Returns:
      List of Contact objects
  """
  try:
    stmt = select(Contact).where(
        (Contact.phone_primary == phone_number) |
        (Contact.phone_secondary == phone_number)
    )
    result = await session.execute(stmt)
    contacts = result.scalars().all()

    logger.debug(f"Found {len(contacts)} contacts for phone: {phone_number}")
    return list(contacts)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get contacts by phone {phone_number}: {e}")
    return []


async def get_contacts_by_company(
    session: AsyncSession,
    company_id: str
) -> List[Contact]:
  """
  Get contacts by company ID.

  Args:
      session: Database session
      company_id: Company ID

  Returns:
      List of Contact objects
  """
  try:
    stmt = select(Contact).where(Contact.company_id == company_id)
    result = await session.execute(stmt)
    contacts = result.scalars().all()

    logger.debug(f"Found {len(contacts)} contacts for company: {company_id}")
    return list(contacts)

  except SQLAlchemyError as e:
    logger.error(f"Failed to get contacts by company {company_id}: {e}")
    return []


async def get_contact_by_phone_primary(
    session: AsyncSession,
    phone_primary: str
) -> Optional[Contact]:
  """
  Get contact by primary phone number.

  Args:
      session: Database session
      phone_primary: Primary phone number

  Returns:
      Contact object or None if not found
  """
  try:
    stmt = select(Contact).where(Contact.phone_primary == phone_primary)
    result = await session.execute(stmt)
    contact = result.scalar_one_or_none()

    if contact:
      logger.debug(f"Found contact by primary phone: {phone_primary}")
    else:
      logger.debug(f"Contact not found by primary phone: {phone_primary}")

    return contact

  except SQLAlchemyError as e:
    logger.error(
        f"Failed to get contact by primary phone {phone_primary}: {e}")
    return None
