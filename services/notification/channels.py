"""
Notification channels implementation.
"""

import asyncio
from typing import Dict, Any, Optional
import json
import re
import httpx

from core.logging.setup import get_logger
from .manager import Notification, NotificationChannel

logger = get_logger(__name__)


class EmailChannel(NotificationChannel):
  """Email notification channel."""

  def __init__(self, smtp_config: Dict[str, Any]):
    """Initialize email channel."""
    self.smtp_config = smtp_config
    self.smtp_host = smtp_config.get("host", "localhost")
    self.smtp_port = smtp_config.get("port", 587)
    self.smtp_username = smtp_config.get("username")
    self.smtp_password = smtp_config.get("password")
    self.use_tls = smtp_config.get("use_tls", True)
    self.from_email = smtp_config.get("from_email", "noreply@example.com")

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


class SlackChannel(NotificationChannel):
  """Slack notification channel."""

  def __init__(self, slack_config: Dict[str, Any]):
    """Initialize Slack channel."""
    self.slack_config = slack_config
    self.bot_token = slack_config.get("bot_token")
    self.webhook_url = slack_config.get("webhook_url")
    self.timeout = slack_config.get("timeout", 30)

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
        "ts": int(notification.created_at)
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
            "https://slack.com/api/chat.postMessage",
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

      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
            self.webhook_url,
            json=teams_message,
            headers={"Content-Type": "application/json"}
        )

        response.raise_for_status()

        logger.info("Teams notification sent successfully")
        return True

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
