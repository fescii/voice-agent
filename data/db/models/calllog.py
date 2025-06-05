"""
Call log database model.
"""
from sqlalchemy import Column, String, Text, DateTime, Enum, Float, Boolean, JSON
from ..base import BaseModel
import enum


class CallStatus(enum.Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NO_ANSWER = "no_answer"
    BUSY = "busy"
    TERMINATED = "terminated"


class CallDirection(enum.Enum):
    """Call direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CallLog(BaseModel):
    """Call log model for tracking call history and metadata."""
    __tablename__ = "call_logs"
    
    # Basic call information
    call_id = Column(String(255), unique=True, index=True, nullable=False)
    ringover_call_id = Column(String(255), index=True)
    agent_id = Column(String(255), index=True, nullable=False)
    
    # Call participants
    caller_number = Column(String(50), nullable=False)
    callee_number = Column(String(50), nullable=False)
    
    # Call metadata
    direction = Column(Enum(CallDirection), nullable=False)
    status = Column(Enum(CallStatus), nullable=False, default=CallStatus.INITIATED)
    
    # Timing information
    initiated_at = Column(DateTime)
    answered_at = Column(DateTime)
    ended_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Audio and transcript
    has_transcript = Column(Boolean, default=False)
    has_recording = Column(Boolean, default=False)
    recording_url = Column(String(500))
    
    # LLM and processing metadata
    llm_provider = Column(String(100))
    tts_provider = Column(String(100))
    stt_provider = Column(String(100))
    
    # Additional metadata
    metadata = Column(JSON)
    error_message = Column(Text)
    
    def __repr__(self):
        return f"<CallLog(call_id='{self.call_id}', status='{self.status}', direction='{self.direction}')>"
