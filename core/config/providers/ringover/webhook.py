"""
Webhook configuration for Ringover.
"""
import os


class WebhookConfig:
  """Ringover webhook configuration."""

  def __init__(self):
    self.webhook_secret = os.getenv("RINGOVER_WEBHOOK_SECRET", "")
    self.webhook_url = os.getenv("RINGOVER_WEBHOOK_URL", "")
