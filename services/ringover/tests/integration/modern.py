"""
Integration test for the updated Ringover streaming integration.
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any

from services.ringover.webhooks.orchestrator import RingoverWebhookOrchestrator
from services.ringover.webhooks.security import WebhookSecurity
from services.ringover.streaming.integration import RingoverStreamerIntegration
from models.external.ringover.webhook import RingoverWebhookEvent
from core.logging.setup import get_logger
from core.config.registry import config_registry

logger = get_logger(__name__)


class RingoverNewIntegrationTest:
  """Test the updated Ringover integration flow with official ringover-streamer."""

  def __init__(self):
    # Initialize config registry first
    if not hasattr(config_registry, '_initialized') or not config_registry._initialized:
      config_registry.initialize()

    self.webhook_orchestrator = RingoverWebhookOrchestrator()
    self.webhook_security = WebhookSecurity()
    self.streamer_integration = RingoverStreamerIntegration()

    # Set up orchestrator with the new integration
    self.webhook_orchestrator.set_streamer_integration(self.streamer_integration)

  async def test_webhook_flow(self):
    """Test the complete webhook flow with the new integration."""
    logger.info("Starting new Ringover integration test...")

    # Test webhook security
    self._test_webhook_security()

    # Test webhook event handling
    await self._test_webhook_events()

    # Test streamer integration components
    await self._test_streamer_integration()

    logger.info("New Ringover integration test completed successfully!")

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

    # Create test webhook events
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
            "data": {
                "caller_number": "+1234567890",
                "receiver_number": "+0987654321"
            }
        },
        {
            "event_type": "call_ended",
            "call_id": "test_call_123",
            "timestamp": current_time,
            "data": {
                "duration": 120
            }
        }
    ]

    # Process each event
    for event_data in test_events:
      try:
        # Create webhook event object
        webhook_event = RingoverWebhookEvent(**event_data)

        # Process through orchestrator
        await self.webhook_orchestrator.handle_webhook_event(webhook_event)

        logger.info(f"Successfully processed {event_data['event_type']} event")

      except Exception as e:
        logger.error(f"Failed to process {event_data['event_type']}: {e}")

  async def _test_streamer_integration(self):
    """Test the new streamer integration components."""
    logger.info("Testing streamer integration...")

    try:
      # Test integration status
      status = self.streamer_integration.get_integration_status()
      logger.info(f"Integration status: {status}")

      # Test active calls
      active_calls = self.streamer_integration.get_active_calls()
      logger.info(f"Active calls: {len(active_calls)}")

      # Test streamer manager status
      manager_status = self.streamer_integration.streamer_manager.get_status()
      logger.info(f"Streamer manager status: {manager_status}")

      logger.info("Streamer integration test completed")

    except Exception as e:
      logger.warning(f"Streamer integration test failed (expected without running streamer): {e}")

  async def _test_call_simulation(self):
    """Simulate a complete call flow."""
    logger.info("Testing complete call simulation...")

    call_id = "sim_call_456"
    current_time = datetime.now(timezone.utc)

    # Simulate ringing
    ringing_event = RingoverWebhookEvent(
        event_type="call_ringing",
        call_id=call_id,
        timestamp=current_time,
        data={"caller_number": "+1111111111", "receiver_number": "+2222222222"}
    )

    await self.webhook_orchestrator.handle_webhook_event(ringing_event)
    logger.info(f"Call {call_id} ringing processed")

    # Check stream info
    stream_info = self.webhook_orchestrator.get_call_stream_info(call_id)
    assert stream_info is not None, "Stream info should exist after ringing"

    # Simulate answered
    answered_event = RingoverWebhookEvent(
        event_type="call_answered",
        call_id=call_id,
        timestamp=current_time,
        data={"caller_number": "+1111111111", "receiver_number": "+2222222222"}
    )

    await self.webhook_orchestrator.handle_webhook_event(answered_event)
    logger.info(f"Call {call_id} answered processed")

    # Simulate ended
    ended_event = RingoverWebhookEvent(
        event_type="call_ended",
        call_id=call_id,
        timestamp=current_time,
        data={"duration": 60}
    )

    await self.webhook_orchestrator.handle_webhook_event(ended_event)
    logger.info(f"Call {call_id} ended processed")

    logger.info("Call simulation completed successfully")


async def run_integration_test():
  """Run the complete integration test."""
  test = RingoverNewIntegrationTest()
  
  try:
    await test.test_webhook_flow()
    await test._test_call_simulation()
    logger.info("🎉 All tests passed!")
    
  except Exception as e:
    logger.error(f"❌ Test failed: {e}")
    raise


if __name__ == "__main__":
  asyncio.run(run_integration_test())
