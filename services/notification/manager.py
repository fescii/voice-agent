"""
Notification manager for handling various types of notifications.

This module provides a unified interface to the modularized notification components.
All classes are now organized in their own files within subdirectories.
"""

# Import all notification components from the modularized structure
from .models.notification import Notification, NotificationPriority, NotificationStatus
from .channels.protocol import NotificationChannel
from .core.manager import NotificationManager

# Maintain backward compatibility
__all__ = [
    "Notification",
    "NotificationPriority",
    "NotificationStatus",
    "NotificationChannel",
    "NotificationManager"
]
