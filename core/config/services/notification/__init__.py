"""
Notification service configuration settings
"""

from .email import EmailConfig
from .slack import SlackConfig

__all__ = ["EmailConfig", "SlackConfig"]
