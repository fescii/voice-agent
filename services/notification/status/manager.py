"""
Notification status manager.
"""

from typing import Dict, Any, Optional, List
from core.logging.setup import get_logger
from ..models.notification import Notification
from ..queue.manager import NotificationQueue

logger = get_logger(__name__)


class NotificationStatusManager:
  """Manages notification status and statistics."""

  def __init__(self, queue: NotificationQueue, sent_notifications: Dict[str, Notification], channels: Dict[str, Any]):
    """Initialize status manager."""
    self.queue = queue
    self.sent_notifications = sent_notifications
    self.channels = channels

  async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a notification.

    Args:
        notification_id: Notification identifier

    Returns:
        Notification status information
    """
    try:
      # Check sent notifications
      if notification_id in self.sent_notifications:
        notification = self.sent_notifications[notification_id]
        return {
            "id": notification.id,
            "status": notification.status.value,
            "created_at": notification.created_at,
            "sent_at": notification.sent_at,
            "retry_count": notification.retry_count,
            "channel": notification.channel,
            "recipient": notification.recipient
        }

      # Check queue
      notification = self.queue.get_by_id(notification_id)
      if notification:
        return {
            "id": notification.id,
            "status": notification.status.value,
            "created_at": notification.created_at,
            "queue_position": self.queue.notifications.index(notification),
            "retry_count": notification.retry_count,
            "channel": notification.channel,
            "recipient": notification.recipient
        }

      return None

    except Exception as e:
      logger.error(f"Error getting notification status: {str(e)}")
      return None

  async def get_queue_stats(self, is_processing: bool) -> Dict[str, Any]:
    """
    Get notification queue statistics.

    Args:
        is_processing: Whether processor is currently running

    Returns:
        Queue statistics
    """
    try:
      return {
          "queue_length": self.queue.size(),
          "is_processing": is_processing,
          "sent_count": len(self.sent_notifications),
          "priority_breakdown": self.queue.get_priority_stats(),
          "channel_breakdown": self.queue.get_channel_stats(),
          "registered_channels": list(self.channels.keys())
      }

    except Exception as e:
      logger.error(f"Error getting queue stats: {str(e)}")
      return {"error": str(e)}
