"""
Email notification channel implementation.
"""

import asyncio
import re
from core.logging.setup import get_logger
from core.config.services.notification.email import EmailConfig
from ...models.notification import Notification
from ...channels.protocol import NotificationChannel

logger = get_logger(__name__)


class EmailChannel(NotificationChannel):
  """Email notification channel."""

  def __init__(self, email_config: EmailConfig):
    """Initialize email channel."""
    self.email_config = email_config
    self.smtp_host = email_config.smtp_host
    self.smtp_port = email_config.smtp_port
    self.smtp_username = email_config.smtp_user
    self.smtp_password = email_config.smtp_password
    self.use_tls = email_config.smtp_use_tls
    self.use_ssl = email_config.smtp_use_ssl
    self.from_email = email_config.from_email
    self.from_name = email_config.from_name

  async def send(self, notification: Notification) -> bool:
    """Send email notification."""
    try:
      logger.info(f"Sending email notification to: {notification.recipient}")

      # In a real implementation, you would use an email library like aiosmtplib
      # For now, we'll simulate the email sending

      email_content = f"""
To: {notification.recipient}
From: {self.from_email}
Subject: {notification.subject}

{notification.message}

---
Notification ID: {notification.id}
Priority: {notification.priority.value}
Type: {notification.type}
"""

      # Simulate email sending
      await asyncio.sleep(0.1)  # Simulate network delay

      logger.info(f"Email sent successfully to: {notification.recipient}")
      return True

    except Exception as e:
      logger.error(f"Failed to send email: {str(e)}")
      return False

  async def validate_recipient(self, recipient: str) -> bool:
    """Validate email address format."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, recipient))
