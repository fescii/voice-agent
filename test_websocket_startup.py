#!/usr/bin/env python3
"""
Test script to validate WebSocket startup service imports and initialization.
"""

import sys
import asyncio
from typing import Dict, Any


async def test_websocket_imports():
  """Test WebSocket service imports."""
  print("Testing WebSocket imports...")

  try:
    # Test WebSocket handlers import
    from wss.handlers import WebSocketHandlers
    print("✓ WebSocketHandlers import successful")

    # Test startup service import
    from core.startup.services.websocket import WebSocketService
    print("✓ WebSocketService import successful")

    return True

  except ImportError as e:
    print(f"✗ Import failed: {e}")
    return False
  except Exception as e:
    print(f"✗ Unexpected error during import: {e}")
    return False


async def test_websocket_service_initialization():
  """Test WebSocket service initialization."""
  print("\nTesting WebSocket service initialization...")

  try:
    from core.startup.services.websocket import WebSocketService
    from core.startup.manager import StartupContext

    # Create service instance
    service = WebSocketService()
    print(
        f"✓ Service created: {service.name} (critical: {service.is_critical})")

    # Create minimal startup context with dict configuration
    class MockConfig:
      def get(self, key, default=None):
        if key == "websocket":
          return {
              "max_connections": 1000,
              "ping_interval": 30
          }
        return default

    context = StartupContext(configuration=MockConfig())

    # Test initialization
    result = await service.initialize(context)
    print(f"✓ Service initialized successfully")
    print(
        f"  - Connection manager: {type(result['connection_manager']).__name__}")
    print(f"  - Orchestrator: {type(result['orchestrator']).__name__}")
    print(f"  - Max connections: {result['max_connections']}")
    print(f"  - Ping interval: {result['ping_interval']}")
    print(f"  - Status: {result['status']}")

    # Test cleanup
    await service.cleanup(context)
    print("✓ Service cleanup completed")

    return True

  except Exception as e:
    print(f"✗ Service initialization failed: {e}")
    import traceback
    traceback.print_exc()
    return False


async def test_websocket_handlers():
  """Test WebSocket handlers orchestrator."""
  print("\nTesting WebSocket handlers orchestrator...")

  try:
    from wss.handlers import WebSocketHandlers

    # Create handlers instance
    handlers = WebSocketHandlers()
    print(f"✓ WebSocketHandlers created")
    print(
        f"  - Connection manager: {type(handlers.connection_manager).__name__}")
    print(f"  - Message handlers: {len(handlers.message_handlers)} registered")

    # List registered handlers
    for handler_type in handlers.message_handlers.keys():
      print(f"    * {handler_type}")

    return True

  except Exception as e:
    print(f"✗ WebSocket handlers test failed: {e}")
    import traceback
    traceback.print_exc()
    return False


async def main():
  """Run all WebSocket tests."""
  print("=== WebSocket Startup Service Test ===\n")

  # Test imports
  imports_ok = await test_websocket_imports()

  if not imports_ok:
    print("\n✗ Import tests failed. Cannot proceed with other tests.")
    sys.exit(1)

  # Test service initialization
  service_ok = await test_websocket_service_initialization()

  # Test handlers
  handlers_ok = await test_websocket_handlers()

  # Summary
  print(f"\n=== Test Summary ===")
  print(f"Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
  print(f"Service: {'✓ PASS' if service_ok else '✗ FAIL'}")
  print(f"Handlers: {'✓ PASS' if handlers_ok else '✗ FAIL'}")

  if all([imports_ok, service_ok, handlers_ok]):
    print("\n🎉 All WebSocket tests passed!")
    sys.exit(0)
  else:
    print("\n❌ Some WebSocket tests failed!")
    sys.exit(1)

if __name__ == "__main__":
  asyncio.run(main())
