"""
Database models for agent memory storage.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Boolean, Table, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime

from data.db.base import BaseModel


class AgentMemory(BaseModel):
  """Agent memory data model."""
  __tablename__ = "agent_memories"

  agent_id = Column(String, nullable=False, index=True)
  conversation_id = Column(String, nullable=False, index=True)
  last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)

  # Memory items stored as collections
  short_term = Column(JSON, default={})
  long_term = Column(JSON, default={})
  working_memory = Column(JSON, default={})

  __table_args__ = (
      # Unique constraint to ensure one memory record per agent/conversation pair
      UniqueConstraint('agent_id', 'conversation_id',
                       name='unique_agent_conversation'),
  )
