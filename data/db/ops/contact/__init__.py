"""Contact operations package."""

from data.db.ops.contact.create import create_contact
from data.db.ops.contact.read import get_contact, get_contacts_by_phone, get_contacts_by_company
from data.db.ops.contact.update import update_contact
from data.db.ops.contact.delete import delete_contact

__all__ = [
    "create_contact",
    "get_contact",
    "get_contacts_by_phone",
    "get_contacts_by_company",
    "update_contact",
    "delete_contact"
]
