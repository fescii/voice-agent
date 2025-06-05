"""
Notification channel protocol and interface.
"""

from typing import Protocol
from ..models.notification import Notification


class NotificationChannel(Protocol):
  """Protocol for notification channels."""

  async def send(self, notification: Notification) -> bool:
    """Send notification through this channel."""
    ...

  async def validate_recipient(self, recipient: str) -> bool:
    """Validate recipient format for this channel."""
    ...
