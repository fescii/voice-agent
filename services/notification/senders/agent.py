"""
Agent notification sender.
"""

import json
import time
from typing import Dict, Any
from core.logging.setup import get_logger
from ..models.notification import NotificationPriority

logger = get_logger(__name__)


class AgentNotificationSender:
  """Handles agent-related notifications."""

  def __init__(self, notification_manager):
    """Initialize agent notification sender."""
    self.notification_manager = notification_manager

  async def send_agent_notification(
      self,
      agent_id: str,
      event_type: str,
      recipient: str,
      details: Dict[str, Any],
      channel: str = "email"
  ) -> str:
    """
    Send agent-related notification.

    Args:
        agent_id: Agent identifier
        event_type: Type of agent event
        recipient: Notification recipient
        details: Event details
        channel: Notification channel

    Returns:
        Notification ID
    """
    try:
      subject = f"Agent {event_type}: {agent_id}"

      message = f"""
Agent Event: {event_type}
Agent ID: {agent_id}
Timestamp: {time.time()}

Details:
{json.dumps(details, indent=2)}
"""

      priority = NotificationPriority.HIGH if event_type in [
          "error", "offline"] else NotificationPriority.NORMAL

      return await self.notification_manager.send_notification(
          notification_type="agent_event",
          recipient=recipient,
          subject=subject,
          message=message,
          channel=channel,
          priority=priority,
          data={
              "agent_id": agent_id,
              "event_type": event_type,
              "details": details
          }
      )

    except Exception as e:
      logger.error(f"Error sending agent notification: {str(e)}")
      raise
