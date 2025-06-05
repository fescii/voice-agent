"""
Notification processing engine.
"""

import asyncio
import time
from typing import Dict
from core.logging.setup import get_logger
from ..models.notification import Notification, NotificationStatus
from ..channels.protocol import NotificationChannel
from ..queue.manager import NotificationQueue

logger = get_logger(__name__)


class NotificationProcessor:
  """Handles notification processing and retry logic."""

  def __init__(self, queue: NotificationQueue, channels: Dict[str, NotificationChannel]):
    """Initialize notification processor."""
    self.queue = queue
    self.channels = channels
    self.sent_notifications: Dict[str, Notification] = {}
    self.is_processing = False
    self.retry_intervals = [60, 300, 900]  # 1min, 5min, 15min

  async def process_queue(self):
    """Process notification queue."""
    try:
      self.is_processing = True
      logger.info("Started processing notification queue")

      while not self.queue.is_empty():
        notification = self.queue.pop()

        try:
          await self._send_notification(notification)
        except Exception as e:
          logger.error(
              f"Error processing notification {notification.id}: {str(e)}")
          await self._handle_failed_notification(notification, str(e))

        # Small delay between notifications
        await asyncio.sleep(0.1)

      logger.info("Finished processing notification queue")

    except Exception as e:
      logger.error(f"Error in notification queue processing: {str(e)}")
    finally:
      self.is_processing = False

  async def _send_notification(self, notification: Notification):
    """Send a single notification."""
    try:
      logger.info(f"Sending notification: {notification.id}")

      channel = self.channels[notification.channel]
      success = await channel.send(notification)

      if success:
        notification.status = NotificationStatus.SENT
        notification.sent_at = time.time()
        self.sent_notifications[notification.id] = notification

        logger.info(f"Successfully sent notification: {notification.id}")
      else:
        raise Exception("Channel send returned False")

    except Exception as e:
      logger.error(f"Failed to send notification {notification.id}: {str(e)}")
      raise

  async def _handle_failed_notification(self, notification: Notification, error: str):
    """Handle failed notification with retry logic."""
    try:
      notification.retry_count += 1
      notification.status = NotificationStatus.FAILED

      if notification.retry_count <= notification.max_retries:
        # Schedule retry
        retry_delay = self.retry_intervals[min(
            notification.retry_count - 1, len(self.retry_intervals) - 1)]

        logger.info(
            f"Scheduling retry for notification {notification.id} in {retry_delay}s")

        # Add back to queue after delay
        asyncio.create_task(self._schedule_retry(notification, retry_delay))
      else:
        logger.error(
            f"Notification {notification.id} failed permanently after {notification.retry_count} attempts")
        self.sent_notifications[notification.id] = notification

        # Could send alert about failed notification here

    except Exception as e:
      logger.error(f"Error handling failed notification: {str(e)}")

  async def _schedule_retry(self, notification: Notification, delay: int):
    """Schedule notification retry after delay."""
    try:
      await asyncio.sleep(delay)

      notification.status = NotificationStatus.RETRY
      await self.queue.add(notification)

      # Start processing if not already running
      if not self.is_processing:
        asyncio.create_task(self.process_queue())

    except Exception as e:
      logger.error(f"Error scheduling retry: {str(e)}")

  async def retry_failed_notifications(self):
    """Manually retry all failed notifications."""
    try:
      failed_notifications = [
          notification for notification in self.sent_notifications.values()
          if notification.status == NotificationStatus.FAILED and
          notification.retry_count < notification.max_retries
      ]

      for notification in failed_notifications:
        notification.status = NotificationStatus.RETRY
        await self.queue.add(notification)

      if failed_notifications and not self.is_processing:
        asyncio.create_task(self.process_queue())

      logger.info(f"Retrying {len(failed_notifications)} failed notifications")

    except Exception as e:
      logger.error(f"Error retrying failed notifications: {str(e)}")
