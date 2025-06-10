"""
Company database model for CRM functionality.
"""
from sqlalchemy import Column, String, Text, DateTime, JSON, Boolean, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from data.db.base import BaseModel
import enum


class CompanyType(enum.Enum):
  """Company type enumeration."""
  PROSPECT = "prospect"
  CUSTOMER = "customer"
  PARTNER = "partner"
  VENDOR = "vendor"
  COMPETITOR = "competitor"
  OTHER = "other"


class CompanySize(enum.Enum):
  """Company size enumeration."""
  STARTUP = "startup"
  SMALL = "small"       # 1-50 employees
  MEDIUM = "medium"     # 51-500 employees
  LARGE = "large"       # 501-5000 employees
  ENTERPRISE = "enterprise"  # 5000+ employees


class Company(BaseModel):
  """Company model for CRM company/account management."""
  __tablename__ = "companies"

  # Basic identification
  external_id = Column(String(255), unique=True, index=True)  # External CRM ID
  company_type = Column(Enum(CompanyType), nullable=False,
                        default=CompanyType.PROSPECT)

  # Company information (only name required)
  name = Column(String(500), nullable=False, index=True)
  legal_name = Column(String(500))
  domain = Column(String(255), index=True)
  website = Column(String(500))

  # Business details
  industry = Column(String(255))
  company_size = Column(Enum(CompanySize))
  annual_revenue = Column(String(50))  # String for flexibility (e.g., "1M-5M")
  employee_count = Column(String(50))  # String for ranges
  founded_year = Column(String(4))

  # Contact information
  phone_main = Column(String(50))
  phone_support = Column(String(50))
  email_main = Column(String(255))
  email_support = Column(String(255))

  # Address information
  address_line1 = Column(String(500))
  address_line2 = Column(String(500))
  city = Column(String(255))
  state = Column(String(100))
  postal_code = Column(String(20))
  country = Column(String(100), default="US")

  # Business relationship
  customer_since = Column(DateTime)
  last_interaction = Column(DateTime)
  account_value = Column(String(50))  # String for flexibility

  # Status and tracking
  is_active = Column(Boolean, default=True)
  is_partner = Column(Boolean, default=False)
  is_competitor = Column(Boolean, default=False)

  # CRM metadata
  crm_source = Column(String(100))  # Which CRM system this came from
  owner_id = Column(String(255), index=True)  # Account manager/owner ID
  parent_company_id = Column(Integer, ForeignKey('companies.id'), index=True)

  # Social and web presence
  linkedin_url = Column(String(500))
  facebook_url = Column(String(500))
  twitter_handle = Column(String(100))

  # Additional data
  tags = Column(JSON)  # Array of tags
  notes = Column(Text)
  custom_fields = Column(JSON)  # For CRM-specific custom fields

  # Relationships
  contacts = relationship("Contact", back_populates="company")
  parent_company = relationship("Company", remote_side="Company.id")

  def __repr__(self):
    return f"<Company(id={self.id}, name='{self.name}', type='{self.company_type}')>"
