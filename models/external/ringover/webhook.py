"""
Pydantic models for Ringover webhook payloads
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class RingoverEventType(str, Enum):
  """Enumeration of supported Ringover webhook event types"""
  CALL_RINGING = "call_ringing"
  CALL_ANSWERED = "call_answered"
  CALL_ENDED = "call_ended"
  MISSED_CALL = "missed_call"
  VOICEMAIL = "voicemail"
  SMS_RECEIVED = "sms_received"
  SMS_SENT = "sms_sent"
  AFTER_CALL_WORK = "after_call_work"
  FAX_RECEIVED = "fax_received"
  # Legacy event types for backward compatibility
  CALL_INITIATED = "call_initiated"
  CALL_FAILED = "call_failed"
  INCOMING_CALL = "incoming_call"
  WEBSOCKET_CONNECTED = "websocket_connected"
  WEBSOCKET_DISCONNECTED = "websocket_disconnected"


class RingoverWebhookEvent(BaseModel):
  """Base model for Ringover webhook events"""
  event_type: str = Field(..., description="Type of the webhook event")
  call_id: Optional[str] = Field(None, description="Ringover call identifier")
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


class CallRingingEvent(RingoverWebhookEvent):
  """Webhook event for calls starting to ring"""
  from_number: str = Field(..., description="Caller phone number")
  to_number: str = Field(..., description="Called phone number")
  direction: str = Field(..., description="Call direction (inbound/outbound)")


class MissedCallEvent(RingoverWebhookEvent):
  """Webhook event for missed calls"""
  caller_number: str = Field(..., description="Caller phone number")
  called_number: str = Field(..., description="Called phone number")
  missed_at: datetime = Field(..., description="When the call was missed")
  duration_before_missed: Optional[int] = Field(
      None, description="Ring duration before missed")


class VoicemailEvent(RingoverWebhookEvent):
  """Webhook event for voicemail messages"""
  caller_number: str = Field(..., description="Caller phone number")
  called_number: str = Field(..., description="Called phone number")
  voicemail_id: str = Field(..., description="Voicemail message ID")
  duration: Optional[int] = Field(
      None, description="Voicemail duration in seconds")
  message_url: Optional[str] = Field(
      None, description="URL to download voicemail")


class SMSReceivedEvent(RingoverWebhookEvent):
  """Webhook event for received SMS messages"""
  from_number: str = Field(..., description="Sender phone number")
  to_number: str = Field(..., description="Recipient phone number")
  message_id: str = Field(..., description="SMS message ID")
  message_content: str = Field(..., description="SMS message text")
  received_at: datetime = Field(..., description="When the SMS was received")


class SMSSentEvent(RingoverWebhookEvent):
  """Webhook event for sent SMS messages"""
  from_number: str = Field(..., description="Sender phone number")
  to_number: str = Field(..., description="Recipient phone number")
  message_id: str = Field(..., description="SMS message ID")
  message_content: str = Field(..., description="SMS message text")
  sent_at: datetime = Field(..., description="When the SMS was sent")
  delivery_status: Optional[str] = Field(None, description="Delivery status")


class AfterCallWorkEvent(RingoverWebhookEvent):
  """Webhook event for after-call work activities"""
  agent_id: str = Field(..., description="Agent performing after-call work")
  work_started_at: datetime = Field(...,
                                    description="When after-call work started")
  work_ended_at: Optional[datetime] = Field(
      None, description="When after-call work ended")
  work_duration: Optional[int] = Field(
      None, description="Duration of after-call work in seconds")
  notes: Optional[str] = Field(None, description="After-call work notes")


class FaxReceivedEvent(RingoverWebhookEvent):
  """Webhook event for received fax messages"""
  from_number: str = Field(..., description="Sender fax number")
  to_number: str = Field(..., description="Recipient fax number")
  fax_id: str = Field(..., description="Fax message ID")
  page_count: Optional[int] = Field(None, description="Number of pages")
  fax_url: Optional[str] = Field(None, description="URL to download fax")
  received_at: datetime = Field(..., description="When the fax was received")
