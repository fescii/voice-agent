"""
Notification channels implementation.

This module provides backward compatibility imports for notification channel classes.
The actual implementations have been modularized into channels/implementations/.
"""

# Import all channel classes from the modularized implementations
from .channels.implementations import (
    EmailChannel,
    WebhookChannel,
    SlackChannel,
    SMSChannel,
    TeamsChannel
)

# Export all channel classes for backward compatibility
__all__ = [
    "EmailChannel",
    "WebhookChannel",
    "SlackChannel",
    "SMSChannel",
    "TeamsChannel"
]
