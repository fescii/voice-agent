"""
System alert notification sender.
"""

import time
from typing import Dict, Any
from core.logging.setup import get_logger
from ..models.notification import NotificationPriority

logger = get_logger(__name__)


class SystemAlertSender:
  """Handles system alert notifications."""

  def __init__(self, notification_manager):
    """Initialize system alert sender."""
    self.notification_manager = notification_manager

  async def send_system_alert(
      self,
      alert_type: str,
      recipient: str,
      message: str,
      severity: str = "medium",
      channel: str = "slack"
  ) -> str:
    """
    Send system alert notification.

    Args:
        alert_type: Type of alert
        recipient: Notification recipient
        message: Alert message
        severity: Alert severity (low, medium, high, critical)
        channel: Notification channel

    Returns:
        Notification ID
    """
    try:
      severity_priority_map = {
          "low": NotificationPriority.LOW,
          "medium": NotificationPriority.NORMAL,
          "high": NotificationPriority.HIGH,
          "critical": NotificationPriority.URGENT
      }

      priority = severity_priority_map.get(
          severity, NotificationPriority.NORMAL)
      subject = f"System Alert: {alert_type} ({severity.upper()})"

      return await self.notification_manager.send_notification(
          notification_type="system_alert",
          recipient=recipient,
          subject=subject,
          message=message,
          channel=channel,
          priority=priority,
          data={
              "alert_type": alert_type,
              "severity": severity,
              "timestamp": time.time()
          }
      )

    except Exception as e:
      logger.error(f"Error sending system alert: {str(e)}")
      raise
