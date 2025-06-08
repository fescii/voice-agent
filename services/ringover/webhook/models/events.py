"""
Webhook event models and enums.
"""
from typing import Dict, Any, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class WebhookEventType(Enum):
  """Ringover webhook event types."""
  CALL_INITIATED = "call.initiated"
  CALL_RINGING = "call.ringing"
  CALL_ANSWERED = "call.answered"
  CALL_ENDED = "call.ended"
  CALL_FAILED = "call.failed"
  CALL_MISSED = "call.missed"
  CALL_TRANSFERRED = "call.transferred"
  CALL_HOLD = "call.hold"
  CALL_UNHOLD = "call.unhold"


@dataclass
class WebhookEvent:
  """Webhook event data structure."""
  event_type: WebhookEventType
  call_id: str
  timestamp: datetime
  data: Dict[str, Any]
  raw_payload: Dict[str, Any]


# Type alias for webhook handler functions
WebhookHandler = Callable[[WebhookEvent], Awaitable[None]]
