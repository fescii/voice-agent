"""
Call notification sender.
"""

import json
import time
from typing import Dict, Any
from core.logging.setup import get_logger
from ..models.notification import NotificationPriority

logger = get_logger(__name__)


class CallNotificationSender:
  """Handles call-related notifications."""

  def __init__(self, notification_manager):
    """Initialize call notification sender."""
    self.notification_manager = notification_manager

  async def send_call_notification(
      self,
      call_id: str,
      event_type: str,
      recipient: str,
      details: Dict[str, Any],
      channel: str = "webhook"
  ) -> str:
    """
    Send call-related notification.

    Args:
        call_id: Call identifier
        event_type: Type of call event
        recipient: Notification recipient
        details: Call details
        channel: Notification channel

    Returns:
        Notification ID
    """
    try:
      subject = f"Call {event_type}: {call_id}"

      message = f"""
Call Event: {event_type}
Call ID: {call_id}
Timestamp: {time.time()}

Details:
{json.dumps(details, indent=2)}
"""

      priority = NotificationPriority.HIGH if event_type in [
          "failed", "error"] else NotificationPriority.NORMAL

      return await self.notification_manager.send_notification(
          notification_type="call_event",
          recipient=recipient,
          subject=subject,
          message=message,
          channel=channel,
          priority=priority,
          data={
              "call_id": call_id,
              "event_type": event_type,
              "details": details
          }
      )

    except Exception as e:
      logger.error(f"Error sending call notification: {str(e)}")
      raise
