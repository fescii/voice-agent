#!/usr/bin/env python3
"""
Simple test script to validate WebSocket handlers import.
"""

import sys


def test_websocket_handlers_import():
  """Test WebSocket handlers import only."""
  print("Testing WebSocket handlers import...")

  try:
    # Test individual handler imports
    from wss.handlers.connection import ConnectionManager
    print("✓ ConnectionManager import successful")

    from wss.handlers.orchestrator import WebSocketHandlers
    print("✓ WebSocketHandlers import successful")

    from wss.handlers import WebSocketHandlers as HandlersFromInit
    print("✓ WebSocketHandlers from __init__ import successful")

    return True

  except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    return False


def test_websocket_handlers_creation():
  """Test WebSocket handlers creation."""
  print("\nTesting WebSocket handlers creation...")

  try:
    from wss.handlers import WebSocketHandlers

    # Create handlers instance
    handlers = WebSocketHandlers()
    print(f"✓ WebSocketHandlers created successfully")
    print(f"  - Message handlers: {len(handlers.message_handlers)} registered")

    # List registered handlers
    for handler_type in handlers.message_handlers.keys():
      print(f"    * {handler_type}")

    print(
        f"  - Connection manager type: {type(handlers.connection_manager).__name__}")

    return True

  except Exception as e:
    print(f"✗ WebSocket handlers creation failed: {e}")
    import traceback
    traceback.print_exc()
    return False


def main():
  """Run WebSocket handlers tests."""
  print("=== WebSocket Handlers Test ===\n")

  # Test imports
  imports_ok = test_websocket_handlers_import()

  if not imports_ok:
    print("\n✗ Import tests failed.")
    sys.exit(1)

  # Test creation
  creation_ok = test_websocket_handlers_creation()

  # Summary
  print(f"\n=== Test Summary ===")
  print(f"Imports: {'✓ PASS' if imports_ok else '✗ FAIL'}")
  print(f"Creation: {'✓ PASS' if creation_ok else '✗ FAIL'}")

  if imports_ok and creation_ok:
    print("\n🎉 All WebSocket handlers tests passed!")
    sys.exit(0)
  else:
    print("\n❌ Some WebSocket handlers tests failed!")
    sys.exit(1)


if __name__ == "__main__":
  main()
