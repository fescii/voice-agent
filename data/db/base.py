"""
Base SQLAlchemy model configuration and utilities.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, Integer, func
from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
  """Base model with common fields and methods."""
  __abstract__ = True

  id = Column(Integer, primary_key=True, index=True)
  created_at = Column(DateTime, default=func.now(), nullable=False)
  updated_at = Column(DateTime, default=func.now(),
                      onupdate=func.now(), nullable=False)

  def to_dict(self) -> dict:
    """Convert model instance to dictionary."""
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}
