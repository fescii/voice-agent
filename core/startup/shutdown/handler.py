"""
Graceful shutdown handler for the application.
"""
import asyncio
import signal
from typing import Optional
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ShutdownHandler:
  """Handles graceful application shutdown."""

  def __init__(self):
    self.shutdown_event = asyncio.Event()
    self._shutdown_initiated = False

  def setup_signal_handlers(self):
    """Setup signal handlers for graceful shutdown."""
    try:
      # Setup signal handlers for graceful shutdown
      signal.signal(signal.SIGTERM, self._signal_handler)
      signal.signal(signal.SIGINT, self._signal_handler)
      logger.info("Signal handlers configured for graceful shutdown")
    except Exception as e:
      logger.warning(f"Could not setup signal handlers: {e}")

  def _signal_handler(self, signum: int, frame):
    """Handle shutdown signals."""
    if not self._shutdown_initiated:
      self._shutdown_initiated = True
      logger.info(f"Received signal {signum}, initiating graceful shutdown...")
      self.shutdown_event.set()

  async def wait_for_shutdown(self):
    """Wait for shutdown signal."""
    await self.shutdown_event.wait()

  def initiate_shutdown(self):
    """Programmatically initiate shutdown."""
    if not self._shutdown_initiated:
      self._shutdown_initiated = True
      logger.info("Programmatic shutdown initiated")
      self.shutdown_event.set()

  @property
  def is_shutting_down(self) -> bool:
    """Check if shutdown is in progress."""
    return self._shutdown_initiated
