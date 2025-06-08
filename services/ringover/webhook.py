"""
Ringover webhook event handler.
"""
import json
from typing import Dict, Any, Optional, Callable, Awaitable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from core.logging.setup import get_logger

logger = get_logger(__name__)


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


WebhookHandler = Callable[[WebhookEvent], Awaitable[None]]


class RingoverWebhookProcessor:
  """
  Processes Ringover webhook events.

  Handles incoming webhook payloads, validates signatures,
  and routes events to appropriate handlers.
  """

  def __init__(self, webhook_secret: Optional[str] = None):
    """
    Initialize webhook processor.

    Args:
        webhook_secret: Optional webhook signature validation secret
    """
    self.webhook_secret = webhook_secret
    self.handlers: Dict[WebhookEventType, list[WebhookHandler]] = {}

  def register_handler(self, event_type: WebhookEventType, handler: WebhookHandler):
    """
    Register a handler for a specific event type.

    Args:
        event_type: Type of webhook event
        handler: Handler function
    """
    if event_type not in self.handlers:
      self.handlers[event_type] = []
    self.handlers[event_type].append(handler)

  def register_global_handler(self, handler: WebhookHandler):
    """
    Register a handler for all event types.

    Args:
        handler: Handler function
    """
    for event_type in WebhookEventType:
      self.register_handler(event_type, handler)

  async def process_webhook(self,
                            payload: Dict[str, Any],
                            signature: Optional[str] = None) -> bool:
    """
    Process a webhook payload.

    Args:
        payload: Webhook payload data
        signature: Optional webhook signature for validation

    Returns:
        True if processed successfully, False otherwise
    """
    # Validate signature if provided
    if self.webhook_secret and signature:
      if not self._validate_signature(payload, signature):
        logger.warning("Webhook signature validation failed")
        return False

    # Parse webhook event
    try:
      event = self._parse_webhook_event(payload)
      if not event:
        logger.warning("Failed to parse webhook event")
        return False

      # Route to handlers
      await self._route_event(event)
      return True

    except Exception as e:
      logger.error(f"Error processing webhook: {e}")
      return False

  def _validate_signature(self, payload: Dict[str, Any], signature: str) -> bool:
    """
    Validate webhook signature.

    Args:
        payload: Webhook payload
        signature: Provided signature

    Returns:
        True if signature is valid, False otherwise
    """
    import hmac
    import hashlib

    if not self.webhook_secret:
      return False

    # Create expected signature
    payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
    expected_signature = hmac.new(
        self.webhook_secret.encode('utf-8'),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

  def _parse_webhook_event(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
    """
    Parse webhook payload into event object.

    Args:
        payload: Raw webhook payload

    Returns:
        Parsed webhook event or None if invalid
    """
    try:
      event_type_str = payload.get("event")
      if not event_type_str:
        logger.warning("Missing event type in webhook payload")
        return None

      # Map event type string to enum
      try:
        event_type = WebhookEventType(event_type_str)
      except ValueError:
        logger.warning(f"Unknown event type: {event_type_str}")
        return None

      call_id = payload.get("call_id")
      if not call_id:
        logger.warning("Missing call_id in webhook payload")
        return None

      # Parse timestamp
      timestamp_str = payload.get("timestamp")
      if timestamp_str:
        timestamp = datetime.fromisoformat(
            timestamp_str.replace('Z', '+00:00'))
      else:
        timestamp = datetime.utcnow()

      # Extract event data
      event_data = payload.get("data", {})

      return WebhookEvent(
          event_type=event_type,
          call_id=call_id,
          timestamp=timestamp,
          data=event_data,
          raw_payload=payload
      )

    except Exception as e:
      logger.error(f"Error parsing webhook event: {e}")
      return None

  async def _route_event(self, event: WebhookEvent):
    """
    Route event to registered handlers.

    Args:
        event: Webhook event to route
    """
    handlers = self.handlers.get(event.event_type, [])

    if not handlers:
      logger.debug(
          f"No handlers registered for event type: {event.event_type}")
      return

    # Execute all handlers concurrently
    import asyncio

    tasks = [handler(event) for handler in handlers]
    try:
      await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
      logger.error(f"Error executing webhook handlers: {e}")


class CallEventProcessor:
  """
  Specialized processor for call-related webhook events.

  Provides higher-level call state management based on
  webhook events from Ringover.
  """

  def __init__(self):
    """Initialize call event processor."""
    self.call_states: Dict[str, Dict[str, Any]] = {}
    self.state_change_handlers: list[Callable[[
        str, str, str], Awaitable[None]]] = []

  def register_state_change_handler(self, handler: Callable[[str, str, str], Awaitable[None]]):
    """
    Register a handler for call state changes.

    Args:
        handler: Function that receives (call_id, old_state, new_state)
    """
    self.state_change_handlers.append(handler)

  async def handle_call_event(self, event: WebhookEvent):
    """
    Handle a call-related webhook event.

    Args:
        event: Webhook event
    """
    call_id = event.call_id
    old_state = self.call_states.get(call_id, {}).get("status")

    # Update call state based on event type
    if event.event_type == WebhookEventType.CALL_INITIATED:
      await self._handle_call_initiated(event)
    elif event.event_type == WebhookEventType.CALL_RINGING:
      await self._handle_call_ringing(event)
    elif event.event_type == WebhookEventType.CALL_ANSWERED:
      await self._handle_call_answered(event)
    elif event.event_type == WebhookEventType.CALL_ENDED:
      await self._handle_call_ended(event)
    elif event.event_type == WebhookEventType.CALL_FAILED:
      await self._handle_call_failed(event)

    # Notify state change handlers
    new_state = self.call_states.get(call_id, {}).get("status")
    if old_state != new_state and new_state:
      await self._notify_state_change(call_id, old_state or "unknown", new_state)

  async def _handle_call_initiated(self, event: WebhookEvent):
    """Handle call initiated event."""
    self.call_states[event.call_id] = {
        "status": "initiated",
        "initiated_at": event.timestamp,
        "data": event.data
    }
    logger.info(f"Call {event.call_id} initiated")

  async def _handle_call_ringing(self, event: WebhookEvent):
    """Handle call ringing event."""
    if event.call_id in self.call_states:
      self.call_states[event.call_id]["status"] = "ringing"
      self.call_states[event.call_id]["ringing_at"] = event.timestamp
    logger.info(f"Call {event.call_id} ringing")

  async def _handle_call_answered(self, event: WebhookEvent):
    """Handle call answered event."""
    if event.call_id in self.call_states:
      self.call_states[event.call_id]["status"] = "answered"
      self.call_states[event.call_id]["answered_at"] = event.timestamp
    logger.info(f"Call {event.call_id} answered")

  async def _handle_call_ended(self, event: WebhookEvent):
    """Handle call ended event."""
    if event.call_id in self.call_states:
      self.call_states[event.call_id]["status"] = "ended"
      self.call_states[event.call_id]["ended_at"] = event.timestamp
      self.call_states[event.call_id]["duration"] = event.data.get("duration")
    logger.info(f"Call {event.call_id} ended")

  async def _handle_call_failed(self, event: WebhookEvent):
    """Handle call failed event."""
    if event.call_id in self.call_states:
      self.call_states[event.call_id]["status"] = "failed"
      self.call_states[event.call_id]["failed_at"] = event.timestamp
      self.call_states[event.call_id]["failure_reason"] = event.data.get(
          "reason")
    logger.info(f"Call {event.call_id} failed")

  async def _notify_state_change(self, call_id: str, old_state: str, new_state: str):
    """Notify registered handlers of state change."""
    import asyncio

    tasks = [handler(call_id, old_state, new_state)
             for handler in self.state_change_handlers]
    try:
      await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as e:
      logger.error(f"Error notifying state change handlers: {e}")

  def get_call_state(self, call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get current state of a call.

    Args:
        call_id: ID of the call

    Returns:
        Call state dictionary or None if not found
    """
    return self.call_states.get(call_id)


class RingoverWebhookConfig:
  """Helper class for Ringover webhook configuration"""

  def __init__(self):
    from core.config.app import ConfigurationManager
    config_manager = ConfigurationManager()
    self.config = config_manager.get_configuration()
    self.base_url = getattr(self.config.telephony_config,
                            'webhook_url', '')

  def get_webhook_endpoint(self) -> str:
    """Get the main webhook endpoint URL"""
    return f"{self.base_url}/api/v1/webhooks/ringover/event"

  def get_webhook_secret(self) -> str:
    """Get the webhook secret for verification"""
    return getattr(self.config.telephony_config, 'webhook_secret', '')

  def get_supported_events(self) -> list[str]:
    """Get list of supported webhook event types"""
    return [
        "call_ringing",
        "call_answered",
        "call_ended",
        "missed_call",
        "voicemail",
        "sms_received",
        "sms_sent",
        "after_call_work",
        "fax_received"
    ]

  def print_configuration_summary(self) -> None:
    """Print webhook configuration summary for setup"""
    print("=== Ringover Webhook Configuration ===")
    print(f"Webhook Endpoint: {self.get_webhook_endpoint()}")
    print(f"Webhook Secret: {self.get_webhook_secret()}")
    print("\nSupported Events:")
    for event in self.get_supported_events():
      print(f"  - {event}")
    print("\nConfiguration Status:")
    print(
        f"  Base URL configured: {'✓' if self.base_url else '✗'}")
    print(f"  Secret configured: {'✓' if self.get_webhook_secret() else '✗'}")
