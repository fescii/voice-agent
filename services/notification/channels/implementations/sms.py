"""
SMS notification channel implementation.
"""

import asyncio
import re
from typing import Dict, Any
from core.logging.setup import get_logger
from ...models.notification import Notification
from ...channels.protocol import NotificationChannel

logger = get_logger(__name__)


class SMSChannel(NotificationChannel):
  """SMS notification channel."""

  def __init__(self, sms_config: Dict[str, Any]):
    """Initialize SMS channel."""
    self.sms_config = sms_config
    self.provider = sms_config.get("provider", "twilio")
    self.api_key = sms_config.get("api_key")
    self.api_secret = sms_config.get("api_secret")
    self.from_number = sms_config.get("from_number")
    self.timeout = sms_config.get("timeout", 30)

  async def send(self, notification: Notification) -> bool:
    """Send SMS notification."""
    try:
      logger.info(f"Sending SMS notification to: {notification.recipient}")

      # Format SMS message (limited to 160 characters)
      sms_text = f"{notification.subject}: {notification.message}"
      if len(sms_text) > 160:
        sms_text = sms_text[:157] + "..."

      if self.provider == "twilio":
        return await self._send_via_twilio(notification.recipient, sms_text)
      else:
        logger.error(f"Unsupported SMS provider: {self.provider}")
        return False

    except Exception as e:
      logger.error(f"Failed to send SMS: {str(e)}")
      return False

  async def _send_via_twilio(self, to_number: str, message: str) -> bool:
    """Send SMS via Twilio."""
    try:
      # Simulate Twilio API call
      # In real implementation, use Twilio SDK

      logger.info(f"Simulating Twilio SMS to {to_number}: {message}")
      await asyncio.sleep(0.2)  # Simulate API delay

      logger.info("SMS sent successfully via Twilio")
      return True

    except Exception as e:
      logger.error(f"Twilio SMS error: {str(e)}")
      return False

  async def validate_recipient(self, recipient: str) -> bool:
    """Validate phone number format."""
    # Basic phone number validation (E.164 format)
    phone_pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(phone_pattern, recipient))
