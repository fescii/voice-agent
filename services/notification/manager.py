"""
Notification manager for handling various types of notifications.
"""

import asyncio
from typing import Dict, Any, Optional, List, Protocol
from enum import Enum
from dataclasses import dataclass
import json
import time

from core.logging.setup import get_logger

logger = get_logger(__name__)


class NotificationPriority(Enum):
  """Notification priority levels."""
  LOW = "low"
  NORMAL = "normal"
  HIGH = "high"
  URGENT = "urgent"


class NotificationStatus(Enum):
  """Notification status."""
  PENDING = "pending"
  SENT = "sent"
  FAILED = "failed"
  RETRY = "retry"


@dataclass
class Notification:
  """Notification data structure."""
  id: str
  type: str
  priority: NotificationPriority
  recipient: str
  subject: str
  message: str
  data: Dict[str, Any]
  channel: str
  status: NotificationStatus = NotificationStatus.PENDING
  created_at: Optional[float] = None
  sent_at: Optional[float] = None
  retry_count: int = 0
  max_retries: int = 3

  def __post_init__(self):
    if self.created_at is None:
      self.created_at = time.time()


class NotificationChannel(Protocol):
  """Protocol for notification channels."""

  async def send(self, notification: Notification) -> bool:
    """Send notification through this channel."""
    ...

  async def validate_recipient(self, recipient: str) -> bool:
    """Validate recipient format for this channel."""
    ...


class NotificationManager:
  """Manages notifications across different channels."""

  def __init__(self):
    """Initialize notification manager."""
    self.channels: Dict[str, NotificationChannel] = {}
    self.notification_queue: List[Notification] = []
    self.sent_notifications: Dict[str, Notification] = {}
    self.is_processing = False
    self.retry_intervals = [60, 300, 900]  # 1min, 5min, 15min

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

      # Add to queue based on priority
      await self._add_to_queue(notification)

      # Start processing if not already running
      if not self.is_processing:
        asyncio.create_task(self._process_queue())

      logger.info(f"Queued notification: {notification_id}")
      return notification_id

    except Exception as e:
      logger.error(f"Error sending notification: {str(e)}")
      raise

  async def _add_to_queue(self, notification: Notification):
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
      insert_index = len(self.notification_queue)
      for i, queued_notification in enumerate(self.notification_queue):
        if priority_order[queued_notification.priority] > notification_priority:
          insert_index = i
          break

      self.notification_queue.insert(insert_index, notification)

      logger.debug(f"Added notification to queue at position {insert_index}")

    except Exception as e:
      logger.error(f"Error adding notification to queue: {str(e)}")
      raise

  async def _process_queue(self):
    """Process notification queue."""
    try:
      self.is_processing = True
      logger.info("Started processing notification queue")

      while self.notification_queue:
        notification = self.notification_queue.pop(0)

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
      await self._add_to_queue(notification)

      # Start processing if not already running
      if not self.is_processing:
        asyncio.create_task(self._process_queue())

    except Exception as e:
      logger.error(f"Error scheduling retry: {str(e)}")

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

      return await self.send_notification(
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

      return await self.send_notification(
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

      return await self.send_notification(
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
      for notification in self.notification_queue:
        if notification.id == notification_id:
          return {
              "id": notification.id,
              "status": notification.status.value,
              "created_at": notification.created_at,
              "queue_position": self.notification_queue.index(notification),
              "retry_count": notification.retry_count,
              "channel": notification.channel,
              "recipient": notification.recipient
          }

      return None

    except Exception as e:
      logger.error(f"Error getting notification status: {str(e)}")
      return None

  async def get_queue_stats(self) -> Dict[str, Any]:
    """
    Get notification queue statistics.

    Returns:
        Queue statistics
    """
    try:
      priority_counts = {
          "urgent": 0,
          "high": 0,
          "normal": 0,
          "low": 0
      }

      for notification in self.notification_queue:
        priority_counts[notification.priority.value] += 1

      channel_counts = {}
      for notification in self.notification_queue:
        channel = notification.channel
        channel_counts[channel] = channel_counts.get(channel, 0) + 1

      return {
          "queue_length": len(self.notification_queue),
          "is_processing": self.is_processing,
          "sent_count": len(self.sent_notifications),
          "priority_breakdown": priority_counts,
          "channel_breakdown": channel_counts,
          "registered_channels": list(self.channels.keys())
      }

    except Exception as e:
      logger.error(f"Error getting queue stats: {str(e)}")
      return {"error": str(e)}

  async def clear_queue(self):
    """Clear the notification queue."""
    try:
      cleared_count = len(self.notification_queue)
      self.notification_queue.clear()

      logger.info(f"Cleared {cleared_count} notifications from queue")

    except Exception as e:
      logger.error(f"Error clearing queue: {str(e)}")

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
        await self._add_to_queue(notification)

      if failed_notifications and not self.is_processing:
        asyncio.create_task(self._process_queue())

      logger.info(f"Retrying {len(failed_notifications)} failed notifications")

    except Exception as e:
      logger.error(f"Error retrying failed notifications: {str(e)}")
