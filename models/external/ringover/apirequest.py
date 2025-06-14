"""
Models for requests to Ringover API
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class RingoverCallRequest(BaseModel):
  """Request model for initiating a call through Ringover"""
  from_number: Optional[int] = Field(
      None, description="Caller ID number (defaults to user's default number if None)")
  to_number: int = Field(..., description="Target phone number")
  timeout: Optional[int] = Field(
      60, description="Seconds before abort (20-300)", ge=20, le=300)
  device: Optional[str] = Field(
      "ALL", description="Device type (ALL, APP, WEB, SIP, MOB, EXT)")
  clir: Optional[bool] = Field(
      False, description="Calling line identification restriction")


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
