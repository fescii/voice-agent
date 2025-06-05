"""
Notification service module.
"""

from .manager import NotificationManager
from .channels import EmailChannel, WebhookChannel, SlackChannel

__all__ = [
    "NotificationManager",
    "EmailChannel",
    "WebhookChannel",
    "SlackChannel"
]
