"""
Complete Ringover configuration combining all components.
"""
from .api import APIConfig
from .webhook import WebhookConfig
from .streaming import StreamingConfig


class RingoverConfig:
  """Complete Ringover configuration."""

  def __init__(self):
    # Initialize all config components
    api_config = APIConfig()
    webhook_config = WebhookConfig()
    streaming_config = StreamingConfig()

    # Expose all properties at the top level for backward compatibility
    self.api_key = api_config.api_key
    self.api_base_url = api_config.api_base_url
    self.api_secret = api_config.api_secret
    self.default_caller_id = api_config.default_caller_id
    self.max_channels = api_config.max_channels
    self.concurrent_limit = api_config.concurrent_limit

    self.webhook_secret = webhook_config.webhook_secret
    self.webhook_url = webhook_config.webhook_url

    self.streamer_auth_token = streaming_config.streamer_auth_token
    self.websocket_url = streaming_config.websocket_url

    # Store components for direct access if needed
    self.api = api_config
    self.webhook = webhook_config
    self.streaming = streaming_config
