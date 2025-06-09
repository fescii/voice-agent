"""
API configuration for Ringover.
"""
import os
from .base import BaseRingoverConfig


class APIConfig(BaseRingoverConfig):
  """Ringover API-specific configuration."""

  def __init__(self):
    super().__init__()
    self.default_caller_id = os.getenv("RINGOVER_DEFAULT_CALLER_ID", "")
    self.max_channels = int(os.getenv("RINGOVER_MAX_CHANNELS", "20"))
    self.concurrent_limit = int(os.getenv("RINGOVER_CONCURRENT_LIMIT", "100"))
