"""
Main Ringover integration module that coordinates webhooks and real-time streaming.
"""
from typing import Optional, Dict, Any
import asyncio

from core.logging.setup import get_logger
from .webhooks.orchestrator import RingoverWebhookOrchestrator
from .webhooks.security import WebhookSecurity
from .streaming.integration import RingoverStreamerIntegration
from services.call.management.orchestrator import CallOrchestrator

logger = get_logger(__name__)


class RingoverIntegration:
  """
  Main integration class that coordinates Ringover webhooks and real-time audio streaming.

  This class implements the complete solution described in the Ringover documentation:
  1. Webhook event notifications for call lifecycle management
  2. Real-time audio streaming via ringover-streamer for bidirectional communication
  3. Security verification of webhook signatures
  4. Coordination between call events and audio stream management
  """

  def __init__(self):
    """Initialize the Ringover integration."""
    self.webhook_orchestrator = RingoverWebhookOrchestrator()
    self.webhook_security = WebhookSecurity()
    self.streamer_integration = RingoverStreamerIntegration()
    self.call_orchestrator: Optional[CallOrchestrator] = None
    self.is_initialized = False

  async def initialize(self, call_orchestrator: CallOrchestrator):
    """
    Initialize the complete Ringover integration.

    Args:
        call_orchestrator: The call orchestrator to coordinate with
    """
    try:
      logger.info("Initializing Ringover integration...")

      # Set up call orchestrator
      self.call_orchestrator = call_orchestrator
      self.webhook_orchestrator.set_call_orchestrator(call_orchestrator)

      # Initialize the streamer integration (installs and starts ringover-streamer)
      await self.streamer_integration.initialize()

      # Connect webhook orchestrator to streamer integration
      self.webhook_orchestrator.set_streamer_integration(
          self.streamer_integration)

      self.is_initialized = True
      logger.info("Ringover integration initialized successfully")

      # Log configuration status
      self._log_integration_status()

    except Exception as e:
      logger.error(f"Failed to initialize Ringover integration: {e}")
      raise

  async def shutdown(self):
    """Shutdown the Ringover integration."""
    try:
      logger.info("Shutting down Ringover integration...")

      # Shutdown streamer integration
      await self.streamer_integration.shutdown()

      self.is_initialized = False
      logger.info("Ringover integration shutdown complete")

    except Exception as e:
      logger.error(f"Error during Ringover integration shutdown: {e}")

  def get_webhook_orchestrator(self) -> RingoverWebhookOrchestrator:
    """Get the webhook orchestrator."""
    return self.webhook_orchestrator

  def get_webhook_security(self) -> WebhookSecurity:
    """Get the webhook security handler."""
    return self.webhook_security

  def get_streamer_integration(self) -> RingoverStreamerIntegration:
    """Get the streamer integration."""
    return self.streamer_integration

  def get_integration_status(self) -> Dict[str, Any]:
    """Get the current status of the integration."""
    streamer_status = self.streamer_integration.get_integration_status()

    return {
        "initialized": self.is_initialized,
        "webhook_security_enabled": self.webhook_security.is_webhook_secure(),
        "streamer_integration": streamer_status,
        "active_calls": self.streamer_integration.get_active_calls(),
        "components": {
            "webhook_orchestrator": bool(self.webhook_orchestrator),
            "webhook_security": bool(self.webhook_security),
            "streamer_integration": bool(self.streamer_integration),
            "call_orchestrator": bool(self.call_orchestrator)
        }
    }

  def _log_integration_status(self):
    """Log the current integration status for debugging."""
    status = self.get_integration_status()

    logger.info("=== Ringover Integration Status ===")
    logger.info(f"Initialized: {status['initialized']}")
    logger.info(
        f"Webhook Security: {'Enabled' if status['webhook_security_enabled'] else 'Disabled'}")
    logger.info(f"Streamer Integration: {status['streamer_integration']}")
    logger.info(f"Active Calls: {len(status['active_calls'])}")

    if not status['webhook_security_enabled']:
      logger.warning(
          "⚠️  Webhook security is not enabled - configure RINGOVER_WEBHOOK_SECRET")

    logger.info("=== Integration Ready ===")


# Global integration instance
_integration: Optional[RingoverIntegration] = None


def get_ringover_integration() -> RingoverIntegration:
  """Get or create the global Ringover integration instance."""
  global _integration
  if _integration is None:
    _integration = RingoverIntegration()
  return _integration


async def initialize_ringover_integration(call_orchestrator: CallOrchestrator):
  """Initialize the Ringover integration with dependencies."""
  integration = get_ringover_integration()
  await integration.initialize(call_orchestrator)
  return integration


async def shutdown_ringover_integration():
  """Shutdown the Ringover integration."""
  integration = get_ringover_integration()
  await integration.shutdown()
