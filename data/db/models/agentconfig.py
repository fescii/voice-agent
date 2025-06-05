"""
Agent configuration database model.
"""
from sqlalchemy import Column, String, Text, Boolean, JSON, Float
from data.db.base import BaseModel


class AgentConfig(BaseModel):
  """Agent configuration model for storing AI agent settings and personas."""
  __tablename__ = "agent_configs"

  # Agent identification
  agent_id = Column(String(255), unique=True, index=True, nullable=False)
  name = Column(String(255), nullable=False)
  description = Column(Text)

  # Agent behavior configuration
  persona_prompt = Column(Text, nullable=False)
  system_instructions = Column(Text)
  voice_id = Column(String(255))  # For TTS

  # LLM configuration
  llm_provider = Column(String(100), nullable=False, default="openai")
  llm_model = Column(String(255), nullable=False, default="gpt-4")
  llm_temperature = Column(Float, default=0.7)
  llm_max_tokens = Column(Float, default=150)

  # TTS configuration
  tts_provider = Column(String(100), nullable=False, default="elevenlabs")
  tts_voice_id = Column(String(255))
  tts_speed = Column(Float, default=1.0)
  tts_stability = Column(Float, default=0.5)

  # STT configuration
  stt_provider = Column(String(100), nullable=False, default="whisper")
  stt_language = Column(String(10), default="en")

  # Agent state and availability
  is_active = Column(Boolean, default=True)
  max_concurrent_calls = Column(Float, default=3)
  current_call_count = Column(Float, default=0)

  # Scheduling and availability
  working_hours = Column(JSON)  # JSON object with schedule
  timezone = Column(String(50), default="UTC")

  # Additional configuration
  custom_config = Column(JSON)  # For provider-specific settings

  def __repr__(self):
    return f"<AgentConfig(agent_id='{self.agent_id}', name='{self.name}', active={self.is_active})>"
