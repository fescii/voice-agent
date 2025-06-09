"""
Startup service for Ringover streamer integration.
"""
import asyncio
from typing import Optional

from core.logging.setup import get_logger
from core.config.registry import config_registry
from .integration import RingoverStreamerIntegration

logger = get_logger(__name__)


class RingoverStreamingStartup:
  """
  Manages the startup and lifecycle of the Ringover streaming integration.

  This service manages the integration with the official ringover-streamer
  and coordinates webhook handling with real-time audio processing.
  """

  def __init__(self):
    """Initialize the startup service."""
    self.integration: Optional[RingoverStreamerIntegration] = None
    self.is_running = False

  async def start_integration(self):
    """
    Start the Ringover streamer integration.
    
    This will:
    1. Initialize the streamer integration
    2. Start the official ringover-streamer service
    3. Set up webhook handling
    """
    try:
      logger.info("Starting Ringover streamer integration...")
      
      # Initialize the integration
      self.integration = RingoverStreamerIntegration()
      await self.integration.initialize()
      
      # Start the integration
      await self.integration.start()
      
      self.is_running = True
      logger.info("Ringover streamer integration started successfully")

      return self.integration

    except Exception as e:
      logger.error(f"Failed to start Ringover streamer integration: {e}")
      raise

  async def stop_integration(self):
    """Stop the streamer integration."""
    if self.integration and self.is_running:
      try:
        logger.info("Stopping Ringover streamer integration...")
        await self.integration.stop()
        self.is_running = False
        logger.info("Ringover streamer integration stopped")
      except Exception as e:
        logger.error(f"Error stopping streamer integration: {e}")

  def get_integration(self) -> Optional[RingoverStreamerIntegration]:
    """Get the active integration instance."""
    return self.integration

  def get_status(self) -> dict:
    """Get status information about the integration."""
    if not self.integration:
      return {
        "is_running": False,
        "streamer_manager_status": "not_initialized",
        "active_calls": []
      }
      
    return {
      "is_running": self.is_running,
      "streamer_manager_status": self.integration.get_streamer_status(),
      "active_calls": list(self.integration.active_calls.keys()),
      "streamer_health": self.integration.streamer_manager.health_check() if self.integration.streamer_manager else "unavailable"
    }
