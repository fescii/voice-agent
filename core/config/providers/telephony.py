"""
Core telephony provider configuration.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TelephonyProvider(Enum):
  """Supported telephony providers."""
  RINGOVER = "ringover"
  TWILIO = "twilio"
  CUSTOM = "custom"


@dataclass
class TelephonyConfig:
  """Base telephony configuration."""
  provider: TelephonyProvider
  api_key: str
  api_secret: Optional[str] = None
  webhook_secret: Optional[str] = None
  base_url: Optional[str] = None
  websocket_url: Optional[str] = None

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "provider": self.provider.value,
        "api_key": self.api_key,
        "api_secret": self.api_secret,
        "webhook_secret": self.webhook_secret,
        "base_url": self.base_url,
        "websocket_url": self.websocket_url
    }


@dataclass
class RingoverConfig(TelephonyConfig):
  """Ringover-specific configuration."""
  business_plan: bool = True
  max_channels_per_agent: int = 20
  concurrent_calls_limit: int = 100

  def __post_init__(self):
    """Set Ringover-specific defaults."""
    if not self.base_url:
      self.base_url = "https://public-api.ringover.com"
    if not self.websocket_url:
      self.websocket_url = "wss://api.ringover.com/ws"
