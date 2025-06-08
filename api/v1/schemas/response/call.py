"""
Pydantic schemas for call-related responses
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum


class CallStatus(str, Enum):
  INITIATED = "initiated"
  RINGING = "ringing"
  ANSWERED = "answered"
  IN_PROGRESS = "in_progress"
  ENDED = "ended"
  FAILED = "failed"
  TERMINATED = "terminated"
  TRANSFERRED = "transferred"


class CallInitiateResponse(BaseModel):
  """Response schema for call initiation"""
  call_id: str = Field(...,
                       description="Unique identifier for the initiated call")
  status: CallStatus = Field(..., description="Current status of the call")
  message: str = Field(..., description="Status message")


class CallTerminateResponse(BaseModel):
  """Response schema for call termination"""
  call_id: str = Field(..., description="ID of the terminated call")
  status: CallStatus = Field(..., description="Final status of the call")
  message: str = Field(..., description="Status message")


class CallTransferResponse(BaseModel):
  """Response schema for call transfer"""
  call_id: str = Field(..., description="ID of the transferred call")
  target_number: str = Field(...,
                             description="Number the call was transferred to")
  status: CallStatus = Field(..., description="Status of the transfer")
  message: str = Field(..., description="Status message")


class CallMuteResponse(BaseModel):
  """Response schema for call mute/unmute"""
  call_id: str = Field(..., description="ID of the call")
  muted: bool = Field(..., description="Current mute status")
  status: str = Field(..., description="Operation status")
  message: str = Field(..., description="Status message")


class CallStatusResponse(BaseModel):
  """Response schema for call status"""
  call_id: str = Field(..., description="Unique identifier for the call")
  status: CallStatus = Field(..., description="Current status of the call")
  agent_id: str = Field(..., description="ID of the agent handling the call")
  phone_number: str = Field(...,
                            description="Phone number involved in the call")
  start_time: Optional[datetime] = Field(
      None, description="When the call started")
  duration: Optional[int] = Field(None, description="Call duration in seconds")
  metadata: Optional[Dict[str, Any]] = Field(
      default_factory=dict, description="Additional call metadata")
