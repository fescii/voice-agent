"""
Webhook configuration management.
"""
from typing import List

from core.logging.setup import get_logger

logger = get_logger(__name__)


class WebhookConfig:
  """Helper class for Ringover webhook configuration."""

  def __init__(self):
    from core.config.registry import config_registry
    self.config = config_registry.ringover
    self.base_url = self.config.webhook_url or ""

  def get_webhook_endpoint(self) -> str:
    """Get the main webhook endpoint URL."""
    return f"{self.base_url}/api/v1/webhooks/ringover/event"

  def get_webhook_secret(self) -> str:
    """Get the webhook secret for verification."""
    return self.config.webhook_secret or ""

  def get_supported_events(self) -> List[str]:
    """Get list of supported webhook event types."""
    return [
        "call_ringing",
        "call_answered",
        "call_ended",
        "missed_call",
        "voicemail",
        "sms_received",
        "sms_sent",
        "after_call_work",
        "fax_received"
    ]

  def print_configuration_summary(self) -> None:
    """Print webhook configuration summary for setup."""
    print("=== Ringover Webhook Configuration ===")
    print(f"Webhook Endpoint: {self.get_webhook_endpoint()}")
    print(f"Webhook Secret: {self.get_webhook_secret()}")
    print("\nSupported Events:")
    for event in self.get_supported_events():
      print(f"  - {event}")
    print("\nConfiguration Status:")
    print(f"  Base URL configured: {'✓' if self.base_url else '✗'}")
    print(f"  Secret configured: {'✓' if self.get_webhook_secret() else '✗'}")

  def is_configured(self) -> bool:
    """Check if webhook is properly configured."""
    return bool(self.base_url and self.get_webhook_secret())
