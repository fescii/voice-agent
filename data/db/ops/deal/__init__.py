"""Deal operations package."""

from data.db.ops.deal.create import create_deal
from data.db.ops.deal.read import get_deal, get_deals_by_contact, get_deals_by_company
from data.db.ops.deal.update import update_deal, update_deal_stage
from data.db.ops.deal.delete import delete_deal

__all__ = [
    "create_deal",
    "get_deal",
    "get_deals_by_contact",
    "get_deals_by_company",
    "update_deal",
    "update_deal_stage",
    "delete_deal"
]
