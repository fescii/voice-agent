"""
Webhook notification channel implementation.
"""

import re
import httpx
from typing import Dict, Any
from core.logging.setup import get_logger
from ...models.notification import Notification
from ...channels.protocol import NotificationChannel

logger = get_logger(__name__)


class WebhookChannel(NotificationChannel):
  """Webhook notification channel."""

  def __init__(self, webhook_config: Dict[str, Any]):
    """Initialize webhook channel."""
    self.webhook_config = webhook_config
    self.timeout = webhook_config.get("timeout", 30)
    self.headers = webhook_config.get("headers", {
        "Content-Type": "application/json",
        "User-Agent": "AI-Voice-Agent/1.0"
    })

  async def send(self, notification: Notification) -> bool:
    """Send webhook notification."""
    try:
      logger.info(f"Sending webhook notification to: {notification.recipient}")

      # Prepare webhook payload
      payload = {
          "notification_id": notification.id,
          "type": notification.type,
          "priority": notification.priority.value,
          "subject": notification.subject,
          "message": notification.message,
          "data": notification.data,
          "timestamp": notification.created_at
      }

      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
            notification.recipient,
            json=payload,
            headers=self.headers
        )

        response.raise_for_status()

        logger.info(f"Webhook sent successfully to: {notification.recipient}")
        return True

    except httpx.HTTPStatusError as e:
      logger.error(
          f"Webhook HTTP error: {e.response.status_code} - {e.response.text}")
      return False
    except Exception as e:
      logger.error(f"Failed to send webhook: {str(e)}")
      return False

  async def validate_recipient(self, recipient: str) -> bool:
    """Validate webhook URL format."""
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(url_pattern, recipient))
