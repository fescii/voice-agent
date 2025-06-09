#!/usr/bin/env python3
"""
Test runner for Ringover service tests.
"""
from core.logging.setup import get_logger
import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


logger = get_logger(__name__)


async def run_integration_tests():
  """Run all integration tests."""
  print("🚀 Running Ringover integration tests...")

  try:
    # Import and run simple test
    sys.path.append(str(Path(__file__).parent))
    from integration.simple import main as simple_test
    print("\n--- Running Simple Integration Test ---")
    await simple_test()

    # Import and run modern test
    from integration.modern import run_integration_test
    print("\n--- Running Modern Integration Test ---")
    await run_integration_test()

    print("\n✅ All integration tests passed!")
    return True

  except Exception as e:
    print(f"\n❌ Integration tests failed: {e}")
    return False


async def run_streaming_tests():
  """Run all streaming tests."""
  print("🚀 Running Ringover streaming tests...")

  try:
    # Import and run complete test
    from streaming.complete import main as complete_test
    print("\n--- Running Complete Streaming Test ---")
    await complete_test()

    print("\n✅ All streaming tests passed!")
    return True

  except Exception as e:
    print(f"\n❌ Streaming tests failed: {e}")
    return False


async def run_all_tests():
  """Run all Ringover tests."""
  print("🏃 Running ALL Ringover service tests...")

  integration_success = await run_integration_tests()
  streaming_success = await run_streaming_tests()

  if integration_success and streaming_success:
    print("\n🎉 All Ringover tests passed!")
    return True
  else:
    print("\n❌ Some Ringover tests failed!")
    return False


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description="Run Ringover service tests")
  parser.add_argument("--type", choices=["integration", "streaming", "all"],
                      default="all", help="Type of tests to run")

  args = parser.parse_args()

  if args.type == "integration":
    asyncio.run(run_integration_tests())
  elif args.type == "streaming":
    asyncio.run(run_streaming_tests())
  else:
    asyncio.run(run_all_tests())
