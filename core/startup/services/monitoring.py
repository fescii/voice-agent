"""
Monitoring service startup initialization.
Handles system monitoring, metrics, and health checks.
"""
from typing import Dict, Any

from .base import BaseStartupService
from core.logging.setup import get_logger

logger = get_logger(__name__)


class MonitoringService(BaseStartupService):
  """Monitoring service startup handler."""

  def __init__(self):
    super().__init__("monitoring", is_critical=False)

  async def initialize(self, context) -> Dict[str, Any]:
    """Initialize monitoring services."""
    try:
      # Get monitoring configuration
      monitoring_config = context.configuration.get("monitoring", {})

      # Initialize basic health metrics
      health_metrics = {
          "startup_time": context.startup_time.isoformat(),
          "healthy_services": context.get_healthy_services(),
          "enabled": monitoring_config.get("enabled", True),
          "interval": monitoring_config.get("interval", 60)  # seconds
      }

      logger.info("Monitoring service initialized successfully")

      return {
          "metrics": health_metrics,
          "status": "ready"
      }

    except Exception as e:
      logger.error(f"Failed to initialize monitoring service: {e}")
      raise

  async def cleanup(self, context) -> None:
    """Cleanup monitoring services."""
    try:
      logger.info("Cleaning up monitoring service...")
      # Most monitoring systems don't require explicit cleanup

    except Exception as e:
      logger.error(f"Error cleaning up monitoring service: {e}")
