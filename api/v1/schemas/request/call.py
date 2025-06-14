"""
Pydantic schemas for call-related requests
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from enum import Enum


class TransferType(str, Enum):
  ATTENDED = "attended"
  BLIND = "blind"


class CallInitiateRequest(BaseModel):
  """Request schema for initiating an outbound call"""
  phone_number: str = Field(..., description="Target phone number to call")
  agent_id: Optional[str] = Field(
      None, description="ID of the agent to handle the call (uses default if not provided)")
  caller_id: Optional[str] = Field(None, description="Caller ID to display")
  context: Optional[Dict[str, Any]] = Field(
      default_factory=dict, description="Additional context for the call")


class CallTerminateRequest(BaseModel):
  """Request schema for terminating a call"""
  call_id: str = Field(..., description="ID of the call to terminate")
  reason: Optional[str] = Field(None, description="Reason for termination")


class CallTransferRequest(BaseModel):
  """Request schema for transferring a call"""
  call_id: str = Field(..., description="ID of the call to transfer")
  target_number: str = Field(..., description="Number to transfer the call to")
  transfer_type: TransferType = Field(
      TransferType.BLIND, description="Type of transfer")


class CallMuteRequest(BaseModel):
  """Request schema for muting/unmuting a call"""
  call_id: str = Field(..., description="ID of the call to mute/unmute")
  muted: bool = Field(...,
                      description="Whether to mute (True) or unmute (False) the call")
