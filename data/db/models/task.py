"""
Task database model for CRM functionality.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, ForeignKey, Enum, Integer
from sqlalchemy.orm import relationship
from data.db.base import BaseModel
import enum


class TaskPriority(enum.Enum):
  """Task priority enumeration."""
  LOW = "low"
  NORMAL = "normal"
  HIGH = "high"
  URGENT = "urgent"


class TaskStatus(enum.Enum):
  """Task status enumeration."""
  NOT_STARTED = "not_started"
  IN_PROGRESS = "in_progress"
  WAITING = "waiting"
  COMPLETED = "completed"
  CANCELLED = "cancelled"
  DEFERRED = "deferred"


class TaskType(enum.Enum):
  """Task type enumeration."""
  FOLLOW_UP = "follow_up"
  CALL_BACK = "call_back"
  SEND_EMAIL = "send_email"
  SEND_PROPOSAL = "send_proposal"
  SCHEDULE_MEETING = "schedule_meeting"
  RESEARCH = "research"
  ADMIN = "admin"
  OTHER = "other"


class Task(BaseModel):
  """Task model for CRM task management and follow-ups."""
  __tablename__ = "tasks"

  # Basic identification
  external_id = Column(String(255), unique=True, index=True)  # External CRM ID
  subject = Column(String(500), nullable=False)
  task_type = Column(Enum(TaskType), default=TaskType.FOLLOW_UP)

  # Task details
  description = Column(Text)
  priority = Column(Enum(TaskPriority), default=TaskPriority.NORMAL)
  status = Column(Enum(TaskStatus), nullable=False,
                  default=TaskStatus.NOT_STARTED)

  # Timing
  due_date = Column(DateTime)
  reminder_date = Column(DateTime)
  completed_date = Column(DateTime)

  # Relationships
  contact_id = Column(Integer, ForeignKey('contacts.id'), index=True)
  company_id = Column(Integer, ForeignKey('companies.id'), index=True)
  deal_id = Column(Integer, ForeignKey('deals.id'), index=True)
  parent_task_id = Column(Integer, ForeignKey('tasks.id'), index=True)

  # Ownership
  owner_id = Column(String(255), index=True, nullable=False)  # Assigned to
  created_by = Column(String(255), index=True)  # Who created it

  # Progress tracking
  completion_percentage = Column(String(3), default="0")  # 0-100 as string
  estimated_hours = Column(String(10))
  actual_hours = Column(String(10))

  # Flags
  is_recurring = Column(Boolean, default=False)
  recurrence_pattern = Column(String(255))  # DAILY, WEEKLY, MONTHLY, etc.
  is_milestone = Column(Boolean, default=False)

  # CRM metadata
  crm_source = Column(String(100))
  tags = Column(JSON)
  custom_fields = Column(JSON)

  # Relationships
  contact = relationship("Contact")
  company = relationship("Company")
  deal = relationship("Deal")
  parent_task = relationship("Task", remote_side="Task.id")

  def __repr__(self):
    return f"<Task(id={self.id}, subject='{self.subject}', status='{self.status}')>"
