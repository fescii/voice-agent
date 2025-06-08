"""
Telephony startup service.
"""
from typing import Dict, Any, TYPE_CHECKING

from .base import BaseStartupService
from services.ringover.api import RingoverAPIClient
from core.config.registry import config_registry
from core.logging.setup import get_logger

if TYPE_CHECKING:
  from core.startup.manager import StartupContext

logger = get_logger(__name__)


class TelephonyService(BaseStartupService):
  """Telephony provider initialization service."""

  def __init__(self):
    super().__init__("telephony", is_critical=False)
    self._api_client = None

  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """Initialize telephony provider and verify connectivity."""
    try:
      # Use centralized config registry
      telephony_config = config_registry.ringover

      # Initialize Ringover API client
      self._api_client = RingoverAPIClient()

      # Test connection by listing active calls (simpler API test)
      async with self._api_client:
        calls = await self._api_client.list_active_calls()

      logger.info("Telephony provider connection verified")

      return {
          "provider": "ringover",
          "api_url": telephony_config.api_base_url,
          "active_calls": len(calls),
          "status": "connected"
      }

    except Exception as e:
      logger.error(f"Telephony initialization failed: {e}")
      # Non-critical service, don't raise
      return {
          "provider": "unknown",
          "status": "error",
          "error": str(e)
      }

  async def cleanup(self, context: "StartupContext") -> None:
    """Cleanup telephony resources."""
    try:
      if self._api_client:
        # API client cleanup happens automatically with async context manager
        pass
      logger.info("Telephony service cleaned up")
    except Exception as e:
      logger.error(f"Error cleaning up telephony service: {e}")

  def get_health_check(self) -> Dict[str, Any]:
    """Get telephony service health information."""
    return {
        "service": self.name,
        "status": "healthy" if self._api_client else "not_initialized",
        "critical": self.is_critical
    }
