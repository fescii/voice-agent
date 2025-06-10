"""
Transcript database model.
"""
from sqlalchemy import Column, String, Text, DateTime, Float, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from data.db.base import BaseModel


class Transcript(BaseModel):
  """Transcript model for storing call transcriptions."""
  __tablename__ = "transcripts"

  # Link to call log
  call_log_id = Column(Integer, ForeignKey(
      "call_logs.id"), nullable=False, index=True)
  call_log = relationship("CallLog", back_populates="transcripts")

  # Transcript metadata
  segment_id = Column(String(255), index=True)  # For real-time segments
  speaker = Column(String(50), nullable=False)  # "caller", "agent", "system"

  # Content
  text = Column(Text, nullable=False)
  confidence_score = Column(Float)  # STT confidence

  # Timing
  start_time = Column(Float)  # Seconds from call start
  end_time = Column(Float)    # Seconds from call start
  timestamp = Column(DateTime, nullable=False)

  # Processing metadata
  stt_provider = Column(String(100))
  language_detected = Column(String(10))
  is_final = Column(Boolean, default=True)  # For streaming transcription

  def __repr__(self):
    return f"<Transcript(call_log_id={self.call_log_id}, speaker='{self.speaker}', text='{self.text[:50]}...')>"
