#!/usr/bin/env python3
"""
Test the complete integration with the running ringover-streamer.
"""
from core.config.registry import config_registry
from core.logging.setup import get_logger
import sys
import os
import asyncio
import json
import websockets
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))


logger = get_logger(__name__)


async def test_streamer_connection():
  """Test direct connection to the ringover-streamer WebSocket."""
  print("Testing direct WebSocket connection to ringover-streamer...")

  try:
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
      print("✅ Connected to ringover-streamer WebSocket")

      # Receive welcome message
      welcome = await websocket.recv()
      welcome_data = json.loads(welcome)
      print(f"✅ Received welcome: {welcome_data}")

      # Send a test call start event
      call_start_event = {
          "event": "call_start",
          "call_id": "test_call_999",
          "timestamp": "2025-06-09T23:05:00Z"
      }

      await websocket.send(json.dumps(call_start_event))
      print("✅ Sent call_start event")

      # Receive response
      response = await websocket.recv()
      response_data = json.loads(response)
      print(f"✅ Received response: {response_data}")

      # Send audio data simulation
      audio_event = {
          "event": "audio_data",
          "call_id": "test_call_999",
          "data": "base64_encoded_audio_data_here"
      }

      await websocket.send(json.dumps(audio_event))
      print("✅ Sent audio_data event")

      # Receive audio acknowledgment
      audio_response = await websocket.recv()
      audio_response_data = json.loads(audio_response)
      print(f"✅ Received audio response: {audio_response_data}")

      # Send call end event
      call_end_event = {
          "event": "call_end",
          "call_id": "test_call_999"
      }

      await websocket.send(json.dumps(call_end_event))
      print("✅ Sent call_end event")

      # Receive end response
      end_response = await websocket.recv()
      end_response_data = json.loads(end_response)
      print(f"✅ Received end response: {end_response_data}")

    print("✅ WebSocket connection test completed successfully")
    return True

  except Exception as e:
    print(f"❌ WebSocket connection test failed: {e}")
    return False


async def test_integration_with_running_streamer():
  """Test our integration components with the actual running streamer."""
  print("\nTesting integration with running ringover-streamer...")

  try:
    # Initialize config registry
    if not hasattr(config_registry, '_initialized') or not config_registry._initialized:
      config_registry.initialize()

    # Import components
    from services.ringover.streaming.integration import RingoverStreamerIntegration
    from services.ringover.streaming.manager import RingoverStreamerManager

    # Create integration
    integration = RingoverStreamerIntegration()

    # Test manager health check
    manager_health = await integration.streamer_manager.health_check()
    print(f"✅ Manager health check: {manager_health}")

    # Test integration status
    status = integration.get_integration_status()
    print(f"✅ Integration status: {status}")

    # Since the streamer is already running, we can test client connectivity
    client_connect_result = await integration.streamer_client.connect()
    print(f"✅ Client connection result: {client_connect_result}")

    return True

  except Exception as e:
    print(f"❌ Integration test failed: {e}")
    import traceback
    traceback.print_exc()
    return False


async def main():
  """Run all tests with the actual ringover-streamer running."""
  print("🚀 Testing Ringover integration with real streamer...")

  # Test direct WebSocket connection
  ws_success = await test_streamer_connection()
  if not ws_success:
    print("❌ WebSocket tests failed")
    return False

  # Test integration components
  integration_success = await test_integration_with_running_streamer()
  if not integration_success:
    print("❌ Integration tests failed")
    return False

  print("\n🎉 All tests passed! The complete Ringover integration is working with the real streamer.")
  return True


if __name__ == "__main__":
  asyncio.run(main())
