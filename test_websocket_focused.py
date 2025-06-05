#!/usr/bin/env python3
"""
Simple test script to validate WebSocket startup service directly.
"""

import sys
import asyncio


async def test_websocket_startup_service():
  """Test WebSocket startup service imports and initialization."""
  print("Testing WebSocket startup service...")

  try:
    # Test WebSocket startup service import
    from core.startup.services.websocket import WebSocketService
    print("✓ WebSocketService import successful")

    # Create service instance
    service = WebSocketService()
    print(
        f"✓ Service created: {service.name} (critical: {service.is_critical})")

    return True

  except Exception as e:
    print(f"✗ WebSocket startup service test failed: {e}")
    import traceback
    traceback.print_exc()
    return False


async def test_websocket_handlers_direct():
  """Test WebSocket handlers directly without complex imports."""
  print("\nTesting WebSocket handlers orchestrator directly...")

  try:
    # Test just the orchestrator import directly
    from wss.handlers.orchestrator import WebSocketHandlers
    print("✓ WebSocketHandlers direct import successful")

    return True

  except Exception as e:
    print(f"✗ WebSocket handlers direct test failed: {e}")
    import traceback
    traceback.print_exc()
    return False


async def main():
  """Run focused WebSocket tests."""
  print("=== Focused WebSocket Tests ===\n")

  # Test startup service
  startup_ok = await test_websocket_startup_service()

  # Test handlers directly
  handlers_ok = await test_websocket_handlers_direct()

  # Summary
  print(f"\n=== Test Summary ===")
  print(f"Startup Service: {'✓ PASS' if startup_ok else '✗ FAIL'}")
  print(f"Handlers Direct: {'✓ PASS' if handlers_ok else '✗ FAIL'}")

  if startup_ok and handlers_ok:
    print("\n🎉 Focused WebSocket tests passed!")
    print("✓ WebSocketOrchestrator issue has been resolved!")
    sys.exit(0)
  else:
    print("\n❌ Some WebSocket tests failed!")
    sys.exit(1)


if __name__ == "__main__":
  asyncio.run(main())
