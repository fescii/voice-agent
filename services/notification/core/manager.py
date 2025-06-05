"""
Main notification manager.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from core.logging.setup import get_logger
from ..models.notification import Notification, NotificationPriority
from ..channels.protocol import NotificationChannel
from ..queue.manager import NotificationQueue
from ..processing.engine import NotificationProcessor
from ..senders.call import CallNotificationSender
from ..senders.agent import AgentNotificationSender
from ..senders.system import SystemAlertSender
from ..status.manager import NotificationStatusManager

logger = get_logger(__name__)


class NotificationManager:
  """Manages notifications across different channels."""

  def __init__(self):
    """Initialize notification manager."""
    self.channels: Dict[str, NotificationChannel] = {}
    self.queue = NotificationQueue()
    self.processor = NotificationProcessor(self.queue, self.channels)
    self.status_manager = NotificationStatusManager(
        self.queue, self.processor.sent_notifications, self.channels)

    # Initialize specialized senders
    self.call_sender = CallNotificationSender(self)
    self.agent_sender = AgentNotificationSender(self)
    self.system_sender = SystemAlertSender(self)

  def register_channel(self, name: str, channel: NotificationChannel):
    """
    Register a notification channel.

    Args:
        name: Channel name
        channel: Channel implementation
    """
    self.channels[name] = channel
    logger.info(f"Registered notification channel: {name}")

  async def send_notification(
      self,
      notification_type: str,
      recipient: str,
      subject: str,
      message: str,
      channel: str,
      priority: NotificationPriority = NotificationPriority.NORMAL,
      data: Optional[Dict[str, Any]] = None
  ) -> str:
    """
    Send a notification.

    Args:
        notification_type: Type of notification
        recipient: Recipient identifier
        subject: Notification subject
        message: Notification message
        channel: Channel to use for sending
        priority: Notification priority
        data: Additional data

    Returns:
        Notification ID
    """
    try:
      # Validate channel
      if channel not in self.channels:
        raise ValueError(f"Unknown notification channel: {channel}")

      # Validate recipient
      channel_impl = self.channels[channel]
      if not await channel_impl.validate_recipient(recipient):
        raise ValueError(
            f"Invalid recipient format for channel {channel}: {recipient}")

      # Create notification
      notification_id = f"{notification_type}_{int(time.time() * 1000)}"

      notification = Notification(
          id=notification_id,
          type=notification_type,
          priority=priority,
          recipient=recipient,
          subject=subject,
          message=message,
          data=data or {},
          channel=channel
      )

      # Add to queue
      await self.queue.add(notification)

      # Start processing if not already running
      if not self.processor.is_processing:
        asyncio.create_task(self.processor.process_queue())

      logger.info(f"Queued notification: {notification_id}")
      return notification_id

    except Exception as e:
      logger.error(f"Error sending notification: {str(e)}")
      raise

  # Delegate specialized sending methods
  async def send_call_notification(self, *args, **kwargs) -> str:
    """Send call-related notification."""
    return await self.call_sender.send_call_notification(*args, **kwargs)

  async def send_agent_notification(self, *args, **kwargs) -> str:
    """Send agent-related notification."""
    return await self.agent_sender.send_agent_notification(*args, **kwargs)

  async def send_system_alert(self, *args, **kwargs) -> str:
    """Send system alert notification."""
    return await self.system_sender.send_system_alert(*args, **kwargs)

  # Delegate status and statistics methods
  async def get_notification_status(self, notification_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a notification."""
    return await self.status_manager.get_notification_status(notification_id)

  async def get_queue_stats(self) -> Dict[str, Any]:
    """Get notification queue statistics."""
    return await self.status_manager.get_queue_stats(self.processor.is_processing)

  async def clear_queue(self):
    """Clear the notification queue."""
    try:
      cleared_count = self.queue.size()
      self.queue.clear()
      logger.info(f"Cleared {cleared_count} notifications from queue")
    except Exception as e:
      logger.error(f"Error clearing queue: {str(e)}")

  async def retry_failed_notifications(self):
    """Manually retry all failed notifications."""
    await self.processor.retry_failed_notifications()
