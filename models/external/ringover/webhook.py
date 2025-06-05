"""
Pydantic models for Ringover webhook payloads
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime


class RingoverWebhookEvent(BaseModel):
  """Base model for Ringover webhook events"""
  event_type: str = Field(..., description="Type of the webhook event")
  call_id: str = Field(..., description="Ringover call identifier")
  timestamp: datetime = Field(..., description="When the event occurred")
  data: Dict[str, Any] = Field(
      default_factory=dict, description="Event-specific data")


class CallInitiatedEvent(RingoverWebhookEvent):
  """Webhook event for call initiation"""
  from_number: str = Field(..., description="Caller phone number")
  to_number: str = Field(..., description="Called phone number")
  direction: str = Field(..., description="Call direction (inbound/outbound)")


class CallAnsweredEvent(RingoverWebhookEvent):
  """Webhook event for call being answered"""
  answered_at: datetime = Field(..., description="When the call was answered")
  answered_by: Optional[str] = Field(None, description="Who answered the call")


class CallEndedEvent(RingoverWebhookEvent):
  """Webhook event for call ending"""
  ended_at: datetime = Field(..., description="When the call ended")
  duration: int = Field(..., description="Call duration in seconds")
  end_reason: str = Field(..., description="Reason for call ending")


class CallFailedEvent(RingoverWebhookEvent):
  """Webhook event for call failure"""
  failed_at: datetime = Field(..., description="When the call failed")
  failure_reason: str = Field(..., description="Reason for call failure")
  error_code: Optional[str] = Field(
      None, description="Error code if available")


class IncomingCallEvent(RingoverWebhookEvent):
  """Webhook event for incoming calls"""
  caller_number: str = Field(..., description="Incoming caller number")
  called_number: str = Field(..., description="Number being called")
  caller_id: Optional[str] = Field(None, description="Caller ID information")


class WebSocketConnectedEvent(RingoverWebhookEvent):
  """Webhook event for WebSocket audio connection established"""
  websocket_url: str = Field(...,
                             description="WebSocket URL for audio streaming")
  audio_format: str = Field(..., description="Audio format for streaming")
  sample_rate: int = Field(..., description="Audio sample rate")


class WebSocketDisconnectedEvent(RingoverWebhookEvent):
  """Webhook event for WebSocket audio connection disconnected"""
  disconnect_reason: str = Field(..., description="Reason for disconnection")
