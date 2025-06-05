"""
Microsoft Teams notification channel implementation.
"""

import httpx
from typing import Dict, Any
from core.logging.setup import get_logger
from ...models.notification import Notification
from ...channels.protocol import NotificationChannel

logger = get_logger(__name__)


class TeamsChannel(NotificationChannel):
  """Microsoft Teams notification channel."""

  def __init__(self, teams_config: Dict[str, Any]):
    """Initialize Teams channel."""
    self.teams_config = teams_config
    self.webhook_url = teams_config.get("webhook_url")
    self.timeout = teams_config.get("timeout", 30)

  async def send(self, notification: Notification) -> bool:
    """Send Teams notification."""
    try:
      logger.info(f"Sending Teams notification to: {notification.recipient}")

      # Format Teams message card
      teams_message = self._format_teams_message(notification)

      if self.webhook_url:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
          response = await client.post(
              self.webhook_url,
              json=teams_message,
              headers={"Content-Type": "application/json"}
          )

          response.raise_for_status()

          logger.info("Teams notification sent successfully")
          return True
      else:
        logger.error("Teams webhook URL not configured")
        return False

    except Exception as e:
      logger.error(f"Failed to send Teams notification: {str(e)}")
      return False

  def _format_teams_message(self, notification: Notification) -> Dict[str, Any]:
    """Format notification for Teams."""
    # Color based on priority
    color_map = {
        "urgent": "FF0000",     # Red
        "high": "FF8C00",       # Orange
        "normal": "36A64F",     # Green
        "low": "808080"         # Gray
    }

    color = color_map.get(notification.priority.value, "36A64F")

    # Create Teams message card
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": notification.subject,
        "sections": [
            {
                "activityTitle": notification.subject,
                "activitySubtitle": f"Priority: {notification.priority.value.capitalize()}",
                "text": notification.message,
                "facts": [
                    {
                        "name": "Notification ID",
                        "value": notification.id
                    },
                    {
                        "name": "Type",
                        "value": notification.type
                    }
                ]
            }
        ]
    }

    # Add additional data
    if notification.data:
      for key, value in notification.data.items():
        if isinstance(value, (str, int, float, bool)):
          message["sections"][0]["facts"].append({
              "name": key.replace("_", " ").title(),
              "value": str(value)
          })

    return message

  async def validate_recipient(self, recipient: str) -> bool:
    """Validate Teams webhook URL."""
    # For Teams, recipient is not used (webhook URL is configured)
    return True
