"""
Notification queue management.
"""

import asyncio
from typing import List, Optional
from core.logging.setup import get_logger
from ..models.notification import Notification, NotificationPriority

logger = get_logger(__name__)


class NotificationQueue:
  """Manages notification queue with priority ordering."""

  def __init__(self):
    """Initialize notification queue."""
    self.notifications: List[Notification] = []

  async def add(self, notification: Notification):
    """Add notification to queue with priority ordering."""
    try:
      # Insert based on priority
      priority_order = {
          NotificationPriority.URGENT: 0,
          NotificationPriority.HIGH: 1,
          NotificationPriority.NORMAL: 2,
          NotificationPriority.LOW: 3
      }

      notification_priority = priority_order[notification.priority]

      # Find insertion point
      insert_index = len(self.notifications)
      for i, queued_notification in enumerate(self.notifications):
        if priority_order[queued_notification.priority] > notification_priority:
          insert_index = i
          break

      self.notifications.insert(insert_index, notification)

      logger.debug(f"Added notification to queue at position {insert_index}")

    except Exception as e:
      logger.error(f"Error adding notification to queue: {str(e)}")
      raise

  def pop(self) -> Notification:
    """Remove and return the next notification from the queue."""
    return self.notifications.pop(0)

  def is_empty(self) -> bool:
    """Check if queue is empty."""
    return len(self.notifications) == 0

  def size(self) -> int:
    """Get queue size."""
    return len(self.notifications)

  def clear(self):
    """Clear the notification queue."""
    self.notifications.clear()

  def get_by_id(self, notification_id: str) -> Optional[Notification]:
    """Find notification by ID in queue."""
    for notification in self.notifications:
      if notification.id == notification_id:
        return notification
    return None

  def get_priority_stats(self) -> dict:
    """Get priority breakdown of queued notifications."""
    priority_counts = {
        "urgent": 0,
        "high": 0,
        "normal": 0,
        "low": 0
    }

    for notification in self.notifications:
      priority_counts[notification.priority.value] += 1

    return priority_counts

  def get_channel_stats(self) -> dict:
    """Get channel breakdown of queued notifications."""
    channel_counts = {}
    for notification in self.notifications:
      channel = notification.channel
      channel_counts[channel] = channel_counts.get(channel, 0) + 1
    return channel_counts
