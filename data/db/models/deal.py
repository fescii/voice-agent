"""
Deal/Opportunity database model for CRM functionality.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, ForeignKey, Enum, Numeric, Integer
from sqlalchemy.orm import relationship
from data.db.base import BaseModel
import enum


class DealStage(enum.Enum):
  """Deal stage enumeration."""
  PROSPECTING = "prospecting"
  QUALIFICATION = "qualification"
  NEEDS_ANALYSIS = "needs_analysis"
  PROPOSAL = "proposal"
  NEGOTIATION = "negotiation"
  CLOSED_WON = "closed_won"
  CLOSED_LOST = "closed_lost"


class DealType(enum.Enum):
  """Deal type enumeration."""
  NEW_BUSINESS = "new_business"
  EXISTING_BUSINESS = "existing_business"
  RENEWAL = "renewal"
  UPSELL = "upsell"
  CROSS_SELL = "cross_sell"


class Deal(BaseModel):
  """Deal/Opportunity model for CRM sales pipeline management."""
  __tablename__ = "deals"

  # Basic identification
  external_id = Column(String(255), unique=True, index=True)  # External CRM ID
  name = Column(String(500), nullable=False, index=True)
  deal_type = Column(Enum(DealType), default=DealType.NEW_BUSINESS)

  # Relationships
  contact_id = Column(Integer, ForeignKey(
      'contacts.id'), nullable=False, index=True)
  company_id = Column(Integer, ForeignKey(
      'companies.id'), nullable=False, index=True)

  # Deal details
  stage = Column(Enum(DealStage), nullable=False,
                 default=DealStage.PROSPECTING)
  amount = Column(String(50))  # String for flexibility
  currency = Column(String(3), default="USD")
  probability = Column(String(10))  # Percentage as string

  # Timeline
  expected_close_date = Column(DateTime)
  actual_close_date = Column(DateTime)

  # Sources and attribution
  lead_source = Column(String(255))
  campaign_source = Column(String(255))

  # Ownership and assignment
  owner_id = Column(String(255), index=True, nullable=False)  # Sales rep ID

  # Status
  is_won = Column(Boolean, default=False)
  is_lost = Column(Boolean, default=False)
  lost_reason = Column(String(500))

  # CRM metadata
  crm_source = Column(String(100))
  tags = Column(JSON)
  notes = Column(Text)
  custom_fields = Column(JSON)

  # Relationships
  contact = relationship("Contact")
  company = relationship("Company")

  def __repr__(self):
    return f"<Deal(id={self.id}, name='{self.name}', stage='{self.stage}', amount='{self.amount}')>"
