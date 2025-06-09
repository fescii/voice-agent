"""
Monitoring service startup initialization.
Handles system monitoring, metrics, and health checks.
"""
import os
from typing import Dict, Any

from .base import BaseStartupService
from core.logging.setup import get_logger

logger = get_logger(__name__)


class MonitoringService(BaseStartupService):
  """Monitoring service startup handler."""

  def __init__(self):
    super().__init__("monitoring", is_critical=True)

  async def initialize(self, context) -> Dict[str, Any]:
    """Initialize monitoring services."""
    try:
      # Get monitoring configuration
      # Get monitoring configuration from environment or use defaults
      monitoring_config = {
          "enabled": os.getenv("MONITORING_ENABLED", "true").lower() == "true",
          "metrics_port": int(os.getenv("METRICS_PORT", "9090")),
      }

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
