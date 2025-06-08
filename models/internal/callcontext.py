"""
Model for ongoing call context and results
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class CallDirection(str, Enum):
  INBOUND = "inbound"
  OUTBOUND = "outbound"


class CallStatus(str, Enum):
  INITIATED = "initiated"
  RINGING = "ringing"
  ANSWERED = "answered"
  IN_PROGRESS = "in_progress"
  ENDED = "ended"
  FAILED = "failed"
  TERMINATED = "terminated"
  TRANSFERRED = "transferred"
  SCHEDULED = "scheduled"


class CallContext(BaseModel):
  """Model representing the context of an ongoing call"""
  call_id: str = Field(..., description="Unique identifier for the call")
  session_id: str = Field(...,
                          description="Session identifier for this call context")
  phone_number: str = Field(...,
                            description="Phone number involved in the call")
  agent_id: str = Field(..., description="ID of the agent handling the call")
  direction: CallDirection = Field(...,
                                   description="Call direction (inbound/outbound)")
  status: CallStatus = Field(..., description="Current status of the call")
  start_time: Optional[datetime] = Field(
      None, description="When the call started")
  end_time: Optional[datetime] = Field(None, description="When the call ended")
  duration: Optional[int] = Field(None, description="Call duration in seconds")
  ringover_call_id: Optional[str] = Field(
      None, description="Ringover's internal call ID")
  websocket_id: Optional[str] = Field(
      None, description="WebSocket connection ID for audio")
  metadata: Dict[str, Any] = Field(
      default_factory=dict, description="Additional call metadata")

  @property
  def is_active(self) -> bool:
    """Check if the call is currently active"""
    return self.status in [CallStatus.ANSWERED, CallStatus.IN_PROGRESS]

  @property
  def is_completed(self) -> bool:
    """Check if the call has completed"""
    return self.status in [CallStatus.ENDED, CallStatus.FAILED, CallStatus.TERMINATED]


class CallResult(BaseModel):
  """Model representing the result of a call operation"""
  call_id: str = Field(..., description="Unique identifier for the call")
  status: CallStatus = Field(..., description="Status of the call operation")
  ringover_call_id: Optional[str] = Field(
      None, description="Ringover's internal call ID")
  error_message: Optional[str] = Field(
      None, description="Error message if operation failed")
  metadata: Dict[str, Any] = Field(
      default_factory=dict, description="Additional result metadata")


class AudioChunk(BaseModel):
  """Model for audio data chunks in WebSocket communication"""
  call_id: str = Field(..., description="Call ID this audio belongs to")
  data: bytes = Field(..., description="Raw audio data")
  timestamp: datetime = Field(
      default_factory=datetime.utcnow, description="When the audio was captured")
  format: str = Field("pcm", description="Audio format (pcm, opus, etc.)")
  sample_rate: int = Field(16000, description="Audio sample rate")
  channels: int = Field(1, description="Number of audio channels")


class TranscriptionResult(BaseModel):
  """Model for speech-to-text transcription results"""
  call_id: str = Field(...,
                       description="Call ID this transcription belongs to")
  text: str = Field(..., description="Transcribed text")
  confidence: float = Field(..., description="Transcription confidence score")
  timestamp: datetime = Field(
      default_factory=datetime.utcnow, description="When the transcription was generated")
  speaker: str = Field("caller", description="Who spoke (caller, agent)")
  language: Optional[str] = Field(None, description="Detected language")


class LLMResponse(BaseModel):
  """Model for LLM response data"""
  call_id: str = Field(..., description="Call ID this response belongs to")
  response_text: str = Field(..., description="LLM generated response text")
  provider: str = Field(..., description="LLM provider used")
  model: str = Field(..., description="Specific model used")
  timestamp: datetime = Field(
      default_factory=datetime.utcnow, description="When the response was generated")
  metadata: Dict[str, Any] = Field(
      default_factory=dict, description="Additional response metadata")
