"""
User profile database model.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean
from ..base import BaseModel


class UserProfile(BaseModel):
  """User/Contact profile model for CRM integration."""
  __tablename__ = "user_profiles"

  # Contact identification
  phone_number = Column(String(50), unique=True, index=True, nullable=False)
  email = Column(String(255), index=True)
  external_id = Column(String(255), index=True)  # CRM system ID

  # Personal information
  first_name = Column(String(255))
  last_name = Column(String(255))
  full_name = Column(String(511))
  company = Column(String(255))
  job_title = Column(String(255))

  # Contact details
  address = Column(Text)
  city = Column(String(255))
  state = Column(String(100))
  postal_code = Column(String(20))
  country = Column(String(100))

  # Communication preferences
  preferred_language = Column(String(10), default="en")
  timezone = Column(String(50))
  communication_consent = Column(Boolean, default=False)

  # CRM metadata
  crm_source = Column(String(100))  # Which CRM this came from
  lead_score = Column(String(50))
  lead_status = Column(String(100))
  tags = Column(JSON)  # Array of tags

  # Interaction history
  last_contact_date = Column(DateTime)
  total_calls = Column(String(50), default="0")
  notes = Column(Text)

  # Additional data
  custom_fields = Column(JSON)  # For CRM-specific fields

  def __repr__(self):
    return f"<UserProfile(phone='{self.phone_number}', name='{self.full_name}')>"
