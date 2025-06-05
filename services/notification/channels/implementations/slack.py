"""
Slack notification channel implementation.
"""

import httpx
from typing import Dict, Any
from core.logging.setup import get_logger
from core.config.services.notification.slack import SlackConfig
from ...models.notification import Notification
from ...channels.protocol import NotificationChannel

logger = get_logger(__name__)


class SlackChannel(NotificationChannel):
  """Slack notification channel."""

  def __init__(self, slack_config: SlackConfig):
    """Initialize Slack channel."""
    self.slack_config = slack_config
    self.bot_token = slack_config.bot_token
    self.webhook_url = slack_config.webhook_url
    self.api_base_url = slack_config.api_base_url
    self.timeout = 30

  async def send(self, notification: Notification) -> bool:
    """Send Slack notification."""
    try:
      logger.info(f"Sending Slack notification to: {notification.recipient}")

      # Prepare Slack message
      slack_message = self._format_slack_message(notification)

      if self.webhook_url:
        # Use incoming webhook
        return await self._send_via_webhook(slack_message)
      elif self.bot_token:
        # Use Slack API
        return await self._send_via_api(notification.recipient, slack_message)
      else:
        logger.error("No Slack configuration found (webhook_url or bot_token)")
        return False

    except Exception as e:
      logger.error(f"Failed to send Slack notification: {str(e)}")
      return False

  def _format_slack_message(self, notification: Notification) -> Dict[str, Any]:
    """Format notification for Slack."""
    # Color based on priority
    color_map = {
        "urgent": "#ff0000",    # Red
        "high": "#ff8c00",      # Orange
        "normal": "#36a64f",    # Green
        "low": "#808080"        # Gray
    }

    color = color_map.get(notification.priority.value, "#36a64f")

    # Create Slack attachment
    attachment = {
        "color": color,
        "title": notification.subject,
        "text": notification.message,
        "fields": [
            {
                "title": "Priority",
                "value": notification.priority.value.capitalize(),
                "short": True
            },
            {
                "title": "Type",
                "value": notification.type,
                "short": True
            },
            {
                "title": "Notification ID",
                "value": notification.id,
                "short": False
            }
        ],
        "footer": "AI Voice Agent",
        "ts": int(notification.created_at or 0)
    }

    # Add additional data fields
    if notification.data:
      for key, value in notification.data.items():
        if isinstance(value, (str, int, float, bool)):
          attachment["fields"].append({
              "title": key.replace("_", " ").title(),
              "value": str(value),
              "short": True
          })

    return {
        "attachments": [attachment]
    }

  async def _send_via_webhook(self, message: Dict[str, Any]) -> bool:
    """Send message via Slack webhook."""
    try:
      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
            self.webhook_url,
            json=message,
            headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()

        logger.info("Slack webhook sent successfully")
        return True

    except Exception as e:
      logger.error(f"Failed to send Slack webhook: {str(e)}")
      return False

  async def _send_via_api(self, channel: str, message: Dict[str, Any]) -> bool:
    """Send message via Slack API."""
    try:
      headers = {
          "Authorization": f"Bearer {self.bot_token}",
          "Content-Type": "application/json"
      }

      payload = {
          "channel": channel,
          **message
      }

      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
            f"{self.api_base_url}/chat.postMessage",
            json=payload,
            headers=headers
        )

        response.raise_for_status()
        result = response.json()

        if result.get("ok"):
          logger.info("Slack API message sent successfully")
          return True
        else:
          logger.error(f"Slack API error: {result.get('error')}")
          return False

    except Exception as e:
      logger.error(f"Failed to send Slack API message: {str(e)}")
      return False

  async def validate_recipient(self, recipient: str) -> bool:
    """Validate Slack channel or user ID format."""
    # Slack channel format: #channel-name or @username or channel ID
    if self.webhook_url:
      # For webhook, recipient is not used
      return True

    # For API, validate channel format
    if recipient.startswith('#') or recipient.startswith('@'):
      return len(recipient) > 1

    # Channel ID format (starts with C, D, or G)
    if recipient.startswith(('C', 'D', 'G')) and len(recipient) >= 9:
      return True

    return False
