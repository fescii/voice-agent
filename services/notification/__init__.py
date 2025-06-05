"""
Notification service module.
"""

from .manager import NotificationManager
# Import channel implementations from the modularized structure
from .channels import EmailChannel, WebhookChannel, SlackChannel, SMSChannel, TeamsChannel

__all__ = [
    "NotificationManager",
    "EmailChannel",
    "WebhookChannel",
    "SlackChannel",
    "SMSChannel",
    "TeamsChannel"
]
