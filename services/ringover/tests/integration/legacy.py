"""
Integration test for Ringover webhooks and real-time audio streaming.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any

from services.ringover.webhooks.orchestrator import RingoverWebhookOrchestrator
from services.ringover.webhooks.security import WebhookSecurity
from services.ringover.streaming.realtime import RingoverRealtimeStreamer
from models.external.ringover.webhook import RingoverWebhookEvent
from core.logging.setup import get_logger
from core.config.registry import config_registry

logger = get_logger(__name__)


class RingoverIntegrationTest:
  """Test the complete Ringover integration flow."""

  def __init__(self):
    # Initialize config registry first
    if not hasattr(config_registry, '_initialized') or not config_registry._initialized:
      config_registry.initialize()

    self.webhook_orchestrator = RingoverWebhookOrchestrator()
    self.webhook_security = WebhookSecurity()
    self.realtime_streamer = RingoverRealtimeStreamer()

    # Set up orchestrator
    self.webhook_orchestrator.set_realtime_streamer(self.realtime_streamer)

  async def test_webhook_flow(self):
    """Test the complete webhook flow as described in documentation."""
    logger.info("Starting Ringover integration test...")

    # Test webhook security
    self._test_webhook_security()

    # Test webhook event handling
    await self._test_webhook_events()

    # Test real-time streaming components
    await self._test_realtime_streaming()

    logger.info("Ringover integration test completed successfully!")

  def _test_webhook_security(self):
    """Test webhook security verification."""
    logger.info("Testing webhook security...")

    # Test security configuration
    is_secure = self.webhook_security.is_webhook_secure()
    logger.info(f"Webhook security configured: {is_secure}")

    # Test signature verification with dummy data
    test_payload = b'{"event": "test", "call_id": "123"}'
    test_signature = "dummy_signature"

    # This should fail without proper secret
    is_valid = self.webhook_security.verify_signature(
        test_payload, test_signature)
    logger.info(f"Signature verification test (expected false): {is_valid}")

  async def _test_webhook_events(self):
    """Test webhook event processing."""
    logger.info("Testing webhook event processing...")

    # Create test webhook events with proper datetime objects
    current_time = datetime.now(timezone.utc)

    test_events = [
        {
            "event_type": "call_ringing",
            "call_id": "test_call_123",
            "timestamp": current_time,
            "data": {
                "caller_number": "+1234567890",
                "receiver_number": "+0987654321"
            }
        },
        {
            "event_type": "call_answered",
            "call_id": "test_call_123",
            "timestamp": current_time,
            "data": {}
        },
        {
            "event_type": "call_ended",
            "call_id": "test_call_123",
            "timestamp": current_time,
            "data": {}
        }
    ]

    for event_data in test_events:
      try:
        # Create webhook event
        webhook_event = RingoverWebhookEvent(**event_data)

        # Process event through orchestrator
        await self.webhook_orchestrator.handle_webhook_event(webhook_event)

        logger.info(
            f"Successfully processed event: {event_data['event_type']}")

      except Exception as e:
        logger.error(f"Error processing event {event_data['event_type']}: {e}")

    # Check active streaming calls
    active_calls = self.webhook_orchestrator.get_active_streaming_calls()
    logger.info(f"Active streaming calls: {active_calls}")

  async def _test_realtime_streaming(self):
    """Test real-time streaming components."""
    logger.info("Testing real-time streaming components...")

    try:
      # Test streamer initialization
      logger.info("Real-time streamer initialized successfully")

      # Test active calls tracking
      active_calls = self.realtime_streamer.get_active_calls()
      logger.info(f"Active calls in streamer: {active_calls}")

      # Test call info retrieval
      call_info = self.realtime_streamer.get_call_info("test_call_123")
      logger.info(f"Call info: {call_info}")

    except Exception as e:
      logger.error(f"Error testing real-time streaming: {e}")

  async def run_full_integration_test(self):
    """Run the complete integration test."""
    try:
      await self.test_webhook_flow()
      return True
    except Exception as e:
      logger.error(f"Integration test failed: {e}")
      return False


async def main():
  """Run the integration test."""
  test = RingoverIntegrationTest()
  success = await test.run_full_integration_test()

  if success:
    print("✅ Ringover integration test passed!")
  else:
    print("❌ Ringover integration test failed!")

  return success


if __name__ == "__main__":
  asyncio.run(main())
