"""
Main webhook processor that coordinates all webhook functionality.
"""
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from .models import WebhookEvent, WebhookEventType, WebhookHandler
from .processing import WebhookValidator, WebhookParser, EventRouter
from .handlers import CallEventHandler
from .configuration import WebhookConfig

logger = get_logger(__name__)


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
        webhook_secret: Secret for webhook signature validation
    """
    self.webhook_secret = webhook_secret

    # Initialize components
    self.validator = WebhookValidator(webhook_secret)
    self.parser = WebhookParser()
    self.router = EventRouter()
    self.call_handler = CallEventHandler()

    # Register call handler for call events
    call_events = [
        WebhookEventType.CALL_INITIATED,
        WebhookEventType.CALL_RINGING,
        WebhookEventType.CALL_ANSWERED,
        WebhookEventType.CALL_ENDED,
        WebhookEventType.CALL_FAILED,
        WebhookEventType.CALL_MISSED,
        WebhookEventType.CALL_TRANSFERRED,
        WebhookEventType.CALL_HOLD,
        WebhookEventType.CALL_UNHOLD
    ]

    for event_type in call_events:
      self.router.register_handler(
          event_type, self.call_handler.handle_call_event)

  def register_handler(self, event_type: WebhookEventType, handler: WebhookHandler):
    """
    Register an event handler for a specific event type.

    Args:
        event_type: Type of event to handle
        handler: Handler function
    """
    self.router.register_handler(event_type, handler)

  def register_global_handler(self, handler: WebhookHandler):
    """
    Register a global handler that receives all events.

    Args:
        handler: Handler function
    """
    self.router.register_global_handler(handler)

  async def process_webhook(self,
                            payload: Dict[str, Any],
                            signature: Optional[str] = None) -> bool:
    """
    Process incoming webhook.

    Args:
        payload: Webhook payload
        signature: Optional signature for validation

    Returns:
        True if processing was successful, False otherwise
    """
    try:
      # Validate signature if provided
      if signature and not self.validator.validate_signature(payload, signature):
        logger.error("Invalid webhook signature")
        return False

      # Parse event
      event = self.parser.parse_webhook_event(payload)
      if not event:
        logger.error("Failed to parse webhook event")
        return False

      logger.info(
          f"Processing webhook event: {event.event_type.value} for call {event.call_id}")

      # Route event to handlers
      await self.router.route_event(event)

      return True

    except Exception as e:
      logger.error(f"Failed to process webhook: {e}")
      return False

  def register_state_change_handler(self, handler):
    """Register a call state change handler."""
    self.call_handler.register_state_change_handler(handler)

  def get_call_state(self, call_id: str) -> Optional[Dict[str, Any]]:
    """Get current call state."""
    return self.call_handler.get_call_state(call_id)


# Legacy alias for backward compatibility
CallEventProcessor = CallEventHandler
