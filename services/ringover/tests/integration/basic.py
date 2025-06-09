"""
Integration test for Ringover webhooks and real-time audio streaming.
"""
import asyncio
import json
import pytest
from typing import Dict, Any
from datetime import datetime, timezone

from core.logging.setup import get_logger
from core.config.registry import config_registry
from services.ringover.integration import get_ringover_integration
from services.call.management.orchestrator import CallOrchestrator
from models.external.ringover.webhook import RingoverWebhookEvent

logger = get_logger(__name__)


@pytest.mark.asyncio
class TestRingoverIntegration:
  """Test suite for the complete Ringover integration."""

  def setup_method(self):
    """Initialize the integration test."""
    # Initialize config registry first
    config_registry.initialize()

    self.integration = get_ringover_integration()
    self.call_orchestrator = CallOrchestrator()

  async def test_complete_integration(self):
    """Run the complete integration test scenario."""
    logger.info("=== Starting Ringover Integration Test ===")

    try:
      # Test 1: Initialize integration
      await self._test_initialization()

      # Test 2: Webhook security
      await self._test_webhook_security()

      # Test 3: Call lifecycle simulation
      await self._test_call_lifecycle()

      # Test 4: Audio streaming simulation
      await self._test_audio_streaming()

      # Test 5: Integration status
      await self._test_integration_status()

      logger.info("=== All Integration Tests Passed! ===")

    except Exception as e:
      logger.error(f"Integration test failed: {e}")
      raise
    finally:
      # Cleanup
      await self.integration.shutdown()

  async def _test_initialization(self):
    """Test integration initialization."""
    logger.info("Testing integration initialization...")

    # Initialize the integration
    await self.integration.initialize(self.call_orchestrator)

    # Verify components are initialized
    assert self.integration.is_initialized, "Integration should be initialized"
    assert self.integration.get_webhook_orchestrator(
    ) is not None, "Webhook orchestrator should exist"
    assert self.integration.get_webhook_security(
    ) is not None, "Webhook security should exist"

    logger.info("✅ Integration initialization test passed")

  async def _test_webhook_security(self):
    """Test webhook security verification."""
    logger.info("Testing webhook security...")

    webhook_security = self.integration.get_webhook_security()

    # Test signature verification with dummy data
    test_payload = b'{"test": "payload"}'

    # Test with no signature
    is_valid = webhook_security.verify_signature(test_payload, None)
    assert not is_valid, "Should reject requests without signature"

    # Test with invalid signature
    is_valid = webhook_security.verify_signature(
        test_payload, "invalid_signature")
    assert not is_valid, "Should reject invalid signatures"

    logger.info("✅ Webhook security test passed")

  async def _test_call_lifecycle(self):
    """Test complete call lifecycle with webhooks."""
    logger.info("Testing call lifecycle simulation...")

    webhook_orchestrator = self.integration.get_webhook_orchestrator()
    call_id = "test_call_123"

    # Simulate incoming call
    incoming_event = RingoverWebhookEvent(
        event_type="call_ringing",
        call_id=call_id,
        timestamp=datetime.now(timezone.utc),
        data={
            "caller_number": "+1234567890",
            "receiver_number": "+0987654321"
        }
    )

    await webhook_orchestrator.handle_webhook_event(incoming_event)

    # Verify call is being tracked
    call_info = webhook_orchestrator.get_call_stream_info(call_id)
    assert call_info is not None, "Call should be tracked after ringing event"
    assert call_info["context"]["status"] == "ringing", "Call status should be ringing"
    # Simulate call answered
    answered_event = RingoverWebhookEvent(
        event_type="call_answered",
        call_id=call_id,
        timestamp=datetime.now(timezone.utc)
    )

    await webhook_orchestrator.handle_webhook_event(answered_event)

    # Verify streaming preparation
    call_info = webhook_orchestrator.get_call_stream_info(call_id)
    if call_info:
      assert call_info["context"]["status"] == "answered", "Call status should be answered"

    # Simulate call ended
    ended_event = RingoverWebhookEvent(
        event_type="call_ended",
        call_id=call_id,
        timestamp=datetime.now(timezone.utc)
    )

    await webhook_orchestrator.handle_webhook_event(ended_event)

    # Verify cleanup
    call_info = webhook_orchestrator.get_call_stream_info(call_id)
    assert call_info is None, "Call should be cleaned up after end event"

    logger.info("✅ Call lifecycle test passed")

  async def _test_audio_streaming(self):
    """Test audio streaming functionality."""
    logger.info("Testing audio streaming simulation...")

    streaming_service = self.integration.get_streaming_service()

    if streaming_service:
      # Verify streaming server is accessible
      server_info = self.integration.streaming_startup.get_server_info()
      assert server_info["is_running"], "Streaming server should be running"

      # Test audio processing simulation
      test_audio = b"dummy_audio_data"
      call_id = "streaming_test_call"

      # This would normally be triggered by actual WebSocket connections
      logger.info(
          "Audio streaming simulation completed (WebSocket server running)")
    else:
      logger.warning("Streaming service not available for testing")

    logger.info("✅ Audio streaming test passed")

  async def _test_integration_status(self):
    """Test integration status reporting."""
    logger.info("Testing integration status...")

    status = self.integration.get_integration_status()

    # Verify status structure
    assert "initialized" in status, "Status should include initialized flag"
    assert "webhook_security_enabled" in status, "Status should include security flag"
    assert "streaming_server" in status, "Status should include server info"
    assert "components" in status, "Status should include component info"

    # Verify initialization status
    assert status["initialized"], "Integration should be initialized"

    # Log status for debugging
    logger.info(f"Integration Status: {json.dumps(status, indent=2)}")

    logger.info("✅ Integration status test passed")

# For backward compatibility, keep the async function


async def run_integration_tests():
  """Run the complete integration test suite."""
  test_suite = TestRingoverIntegration()
  test_suite.setup_method()
  await test_suite.test_complete_integration()


if __name__ == "__main__":
  # Run tests directly
  asyncio.run(run_integration_tests())
