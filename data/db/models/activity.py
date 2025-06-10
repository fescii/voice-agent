"""
Activity database model for CRM functionality.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from data.db.base import BaseModel
import enum


class ActivityType(enum.Enum):
  """Activity type enumeration."""
  CALL = "call"
  EMAIL = "email"
  MEETING = "meeting"
  TASK = "task"
  NOTE = "note"
  SMS = "sms"
  VOICEMAIL = "voicemail"
  DEMO = "demo"
  PROPOSAL = "proposal"
  FOLLOW_UP = "follow_up"
  OTHER = "other"


class ActivityStatus(enum.Enum):
  """Activity status enumeration."""
  PLANNED = "planned"
  IN_PROGRESS = "in_progress"
  COMPLETED = "completed"
  CANCELLED = "cancelled"
  NO_SHOW = "no_show"


class ActivityDirection(enum.Enum):
  """Activity direction enumeration."""
  INBOUND = "inbound"
  OUTBOUND = "outbound"
  INTERNAL = "internal"


class Activity(BaseModel):
  """Activity model for CRM interaction tracking."""
  __tablename__ = "activities"

  # Basic identification
  external_id = Column(String(255), unique=True, index=True)  # External CRM ID
  activity_type = Column(Enum(ActivityType), nullable=False)
  subject = Column(String(500), nullable=False)

  # Relationships
  contact_id = Column(Integer, ForeignKey('contacts.id'), index=True)
  company_id = Column(Integer, ForeignKey('companies.id'), index=True)
  deal_id = Column(Integer, ForeignKey('deals.id'), index=True)

  # Activity details
  direction = Column(Enum(ActivityDirection),
                     default=ActivityDirection.OUTBOUND)
  status = Column(Enum(ActivityStatus), nullable=False,
                  default=ActivityStatus.PLANNED)

  # Timing
  scheduled_at = Column(DateTime)
  started_at = Column(DateTime)
  completed_at = Column(DateTime)
  duration_minutes = Column(String(10))  # Duration as string

  # Content
  description = Column(Text)
  outcome = Column(Text)

  # Ownership
  # User who performed/scheduled
  owner_id = Column(String(255), index=True, nullable=False)
  # Can be assigned to someone else
  assigned_to = Column(String(255), index=True)

  # Call-specific fields (when activity_type = CALL)
  call_id = Column(String(255), index=True)  # Reference to call_logs table
  phone_number = Column(String(50))
  recording_url = Column(String(1000))

  # Email-specific fields
  email_thread_id = Column(String(255))
  email_subject = Column(String(500))

  # Meeting-specific fields
  meeting_url = Column(String(1000))
  meeting_location = Column(String(500))

  # Flags
  is_private = Column(Boolean, default=False)
  requires_follow_up = Column(Boolean, default=False)
  follow_up_date = Column(DateTime)

  # CRM metadata
  crm_source = Column(String(100))
  tags = Column(JSON)
  custom_fields = Column(JSON)

  # Relationships
  contact = relationship("Contact")
  company = relationship("Company")
  deal = relationship("Deal")

  def __repr__(self):
    return f"<Activity(id={self.id}, type='{self.activity_type}', subject='{self.subject}')>"
