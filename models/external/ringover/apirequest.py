"""
Models for requests to Ringover API
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class RingoverCallRequest(BaseModel):
  """Request model for initiating a call through Ringover"""
  call_id: str = Field(..., description="Internal call identifier")
  from_number: str = Field(..., description="Caller ID number")
  to_number: str = Field(..., description="Target phone number")
  agent_id: str = Field(..., description="Agent handling the call")
  context: Dict[str, Any] = Field(
      default_factory=dict, description="Additional call context")


class RingoverTransferRequest(BaseModel):
  """Request model for transferring a call"""
  call_id: str = Field(..., description="Call to transfer")
  target_number: str = Field(..., description="Number to transfer to")
  transfer_type: str = Field(
      "blind", description="Type of transfer (blind/attended)")


class RingoverHangupRequest(BaseModel):
  """Request model for hanging up a call"""
  call_id: str = Field(..., description="Call to hang up")
  reason: Optional[str] = Field(None, description="Reason for hangup")


class RingoverMuteRequest(BaseModel):
  """Request model for muting/unmuting a call"""
  call_id: str = Field(..., description="Call to mute/unmute")
  muted: bool = Field(..., description="Whether to mute or unmute")
