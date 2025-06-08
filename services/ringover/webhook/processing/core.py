"""
Core webhook processing functionality.
"""
import json
import hmac
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from core.logging.setup import get_logger
from ..models import WebhookEvent, WebhookEventType, WebhookHandler

logger = get_logger(__name__)


class WebhookValidator:
  """Handles webhook signature validation."""

  def __init__(self, webhook_secret: Optional[str] = None):
    self.webhook_secret = webhook_secret

  def validate_signature(self, payload: Dict[str, Any], signature: str) -> bool:
    """
    Validate webhook signature.

    Args:
        payload: Webhook payload
        signature: Provided signature

    Returns:
        True if signature is valid, False otherwise
    """
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


class WebhookParser:
  """Handles webhook event parsing."""

  def parse_webhook_event(self, payload: Dict[str, Any]) -> Optional[WebhookEvent]:
    """
    Parse webhook payload into event object.

    Args:
        payload: Raw webhook payload

    Returns:
        WebhookEvent object or None if parsing fails
    """
    try:
      # Extract event type
      event_type_str = payload.get("event", payload.get("type"))
      if not event_type_str:
        logger.error("No event type found in webhook payload")
        return None

      # Map to enum
      try:
        event_type = WebhookEventType(event_type_str)
      except ValueError:
        logger.warning(f"Unknown event type: {event_type_str}")
        return None

      # Extract call ID
      call_id = payload.get("call_id", payload.get("id"))
      if not call_id:
        logger.error("No call ID found in webhook payload")
        return None

      # Extract timestamp
      timestamp_str = payload.get("timestamp", payload.get("created_at"))
      if timestamp_str:
        try:
          timestamp = datetime.fromisoformat(
              timestamp_str.replace('Z', '+00:00'))
        except ValueError:
          timestamp = datetime.now(timezone.utc)
      else:
        timestamp = datetime.now(timezone.utc)

      # Extract additional data
      data = payload.get("data", {})

      return WebhookEvent(
          event_type=event_type,
          call_id=call_id,
          timestamp=timestamp,
          data=data,
          raw_payload=payload
      )

    except Exception as e:
      logger.error(f"Failed to parse webhook event: {e}")
      return None


class EventRouter:
  """Routes webhook events to appropriate handlers."""

  def __init__(self):
    self._handlers: Dict[WebhookEventType, List[WebhookHandler]] = {}
    self._global_handlers: List[WebhookHandler] = []

  def register_handler(self, event_type: WebhookEventType, handler: WebhookHandler):
    """
    Register an event handler for a specific event type.

    Args:
        event_type: Type of event to handle
        handler: Handler function
    """
    if event_type not in self._handlers:
      self._handlers[event_type] = []
    self._handlers[event_type].append(handler)
    logger.info(f"Registered handler for {event_type.value}")

  def register_global_handler(self, handler: WebhookHandler):
    """
    Register a global handler that receives all events.

    Args:
        handler: Handler function
    """
    self._global_handlers.append(handler)
    logger.info("Registered global webhook handler")

  async def route_event(self, event: WebhookEvent):
    """
    Route event to appropriate handlers.

    Args:
        event: Webhook event to route
    """
    try:
      # Call global handlers first
      for handler in self._global_handlers:
        try:
          await handler(event)
        except Exception as e:
          logger.error(f"Global handler failed: {e}")

      # Call specific event handlers
      if event.event_type in self._handlers:
        for handler in self._handlers[event.event_type]:
          try:
            await handler(event)
          except Exception as e:
            logger.error(
                f"Event handler failed for {event.event_type.value}: {e}")

    except Exception as e:
      logger.error(f"Failed to route event {event.event_type.value}: {e}")
