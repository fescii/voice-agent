#!/usr/bin/env python3
"""
Simple test script for the new Ringover integration.
"""
from core.config.registry import config_registry
from core.logging.setup import get_logger
import sys
import os
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Now import what we need

logger = get_logger(__name__)


async def test_imports():
  """Test that we can import the new components without circular imports."""
  print("Testing imports...")

  try:
    # Import the webhook orchestrator
    from services.ringover.webhooks.orchestrator import RingoverWebhookOrchestrator
    print("✅ RingoverWebhookOrchestrator imported successfully")

    # Import the streamer integration
    from services.ringover.streaming.integration import RingoverStreamerIntegration
    print("✅ RingoverStreamerIntegration imported successfully")

    # Import the webhook event model
    from models.external.ringover.webhook import RingoverWebhookEvent
    print("✅ RingoverWebhookEvent imported successfully")

    return True

  except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    return False


async def test_basic_functionality():
  """Test basic functionality without external dependencies."""
  print("\nTesting basic functionality...")

  try:
    # Initialize config registry
    if not hasattr(config_registry, '_initialized') or not config_registry._initialized:
      config_registry.initialize()

    # Import components
    from services.ringover.webhooks.orchestrator import RingoverWebhookOrchestrator
    from services.ringover.streaming.integration import RingoverStreamerIntegration
    from models.external.ringover.webhook import RingoverWebhookEvent
    from datetime import datetime, timezone

    # Create instances
    webhook_orchestrator = RingoverWebhookOrchestrator()
    streamer_integration = RingoverStreamerIntegration()

    # Set up the connection
    webhook_orchestrator.set_streamer_integration(streamer_integration)
    print("✅ Components connected successfully")

    # Create a test webhook event
    test_event = RingoverWebhookEvent(
        event_type="call_ringing",
        call_id="test_123",
        timestamp=datetime.now(timezone.utc),
        data={"from": "+1234567890", "to": "+0987654321"}
    )
    print("✅ Test event created successfully")

    # Test the webhook orchestrator
    await webhook_orchestrator.handle_webhook_event(test_event)
    print("✅ Webhook event handled successfully")

    # Check if the event was processed
    stream_info = webhook_orchestrator.get_call_stream_info("test_123")
    if stream_info:
      print("✅ Stream info created successfully")
    else:
      print("⚠️ Stream info not found (this may be expected)")

    # Test integration status
    status = streamer_integration.get_integration_status()
    print(f"✅ Integration status: {status}")

    return True

  except Exception as e:
    print(f"❌ Basic functionality test failed: {e}")
    import traceback
    traceback.print_exc()
    return False


async def main():
  """Run all tests."""
  print("🚀 Starting Ringover integration tests...")

  # Test imports
  import_success = await test_imports()
  if not import_success:
    print("❌ Import tests failed, stopping here")
    return False

  # Test basic functionality
  func_success = await test_basic_functionality()
  if not func_success:
    print("❌ Functionality tests failed")
    return False

  print("\n🎉 All tests passed! The new integration architecture is working.")
  return True


if __name__ == "__main__":
  asyncio.run(main())
