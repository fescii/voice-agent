"""
Contact database model for CRM functionality.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from data.db.base import BaseModel
import enum


class ContactType(enum.Enum):
  """Contact type enumeration."""
  LEAD = "lead"
  PROSPECT = "prospect"
  CUSTOMER = "customer"
  PARTNER = "partner"
  VENDOR = "vendor"
  OTHER = "other"


class LeadStatus(enum.Enum):
  """Lead status enumeration."""
  NEW = "new"
  CONTACTED = "contacted"
  QUALIFIED = "qualified"
  PROPOSAL = "proposal"
  NEGOTIATION = "negotiation"
  CLOSED_WON = "closed_won"
  CLOSED_LOST = "closed_lost"
  DORMANT = "dormant"


class Contact(BaseModel):
  """Contact model for CRM contact management."""
  __tablename__ = "contacts"

  # Basic identification
  external_id = Column(String(255), unique=True, index=True)  # External CRM ID
  contact_type = Column(Enum(ContactType), nullable=False,
                        default=ContactType.LEAD)

  # Contact information (only phone required for voice system)
  phone_primary = Column(String(50), unique=True, index=True, nullable=False)
  phone_secondary = Column(String(50), index=True)
  email_primary = Column(String(255), index=True)
  email_secondary = Column(String(255))

  # Personal information
  first_name = Column(String(255))
  last_name = Column(String(255))
  full_name = Column(String(511))  # Computed field
  title = Column(String(255))

  # Company relationship
  company_id = Column(Integer, ForeignKey('companies.id'), index=True)
  company = relationship("Company", back_populates="contacts")

  # Address information
  address_line1 = Column(String(500))
  address_line2 = Column(String(500))
  city = Column(String(255))
  state = Column(String(100))
  postal_code = Column(String(20))
  country = Column(String(100), default="US")

  # Lead/Sales information
  lead_status = Column(Enum(LeadStatus), default=LeadStatus.NEW)
  lead_score = Column(String(10))  # Score as string for flexibility
  lead_source = Column(String(255))

  # Communication preferences
  preferred_language = Column(String(10), default="en")
  timezone = Column(String(50))
  do_not_call = Column(Boolean, default=False)
  do_not_email = Column(Boolean, default=False)
  communication_consent = Column(Boolean, default=False)

  # Interaction tracking
  last_contact_date = Column(DateTime)
  next_follow_up = Column(DateTime)
  total_calls = Column(String(10), default="0")
  total_emails = Column(String(10), default="0")

  # CRM metadata
  crm_source = Column(String(100))  # Which CRM system this came from
  owner_id = Column(String(255), index=True)  # Sales rep/owner ID
  tags = Column(JSON)  # Array of tags
  notes = Column(Text)

  # Additional data
  custom_fields = Column(JSON)  # For CRM-specific custom fields

  def __repr__(self):
    return f"<Contact(id={self.id}, name='{self.full_name}', phone='{self.phone_primary}')>"
