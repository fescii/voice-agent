#!/usr/bin/env python3
"""
Master test runner for the entire voice project.
"""
from core.logging.setup import get_logger
import sys
import asyncio
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


logger = get_logger(__name__)


def run_test_suite(test_path: str, suite_name: str) -> bool:
  """Run a test suite and return success status."""
  print(f"\n{'='*50}")
  print(f"Running {suite_name} Tests")
  print(f"{'='*50}")

  try:
    result = subprocess.run([
        sys.executable, str(test_path)
    ], cwd=project_root, capture_output=True, text=True)

    print(result.stdout)
    if result.stderr:
      print("STDERR:", result.stderr)

    if result.returncode == 0:
      print(f"✅ {suite_name} tests PASSED")
      return True
    else:
      print(f"❌ {suite_name} tests FAILED (exit code: {result.returncode})")
      return False

  except Exception as e:
    print(f"❌ {suite_name} tests FAILED with exception: {e}")
    return False


async def run_all_tests():
  """Run all test suites in the project."""
  print("🚀 Running ALL project tests...")

  test_suites = [
      ("services/ringover/tests/runner.py", "Ringover Service"),
      ("services/agent/tests/runner.py", "Agent Service"),
      ("api/tests/runner.py", "API"),
  ]

  results = []
  for test_path, suite_name in test_suites:
    full_path = project_root / test_path
    if full_path.exists():
      success = run_test_suite(str(full_path), suite_name)
      results.append((suite_name, success))
    else:
      print(f"⚠️  Test suite not found: {test_path}")
      results.append((suite_name, False))

  # Summary
  print(f"\n{'='*60}")
  print("TEST SUMMARY")
  print(f"{'='*60}")

  all_passed = True
  for suite_name, success in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{suite_name:<30} {status}")
    if not success:
      all_passed = False

  print(f"{'='*60}")
  if all_passed:
    print("🎉 ALL TESTS PASSED!")
    return True
  else:
    print("❌ SOME TESTS FAILED!")
    return False


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(description="Run project tests")
  parser.add_argument("--service", choices=["ringover", "agent", "api", "all"],
                      default="all", help="Service tests to run")

  args = parser.parse_args()

  if args.service == "ringover":
    success = run_test_suite(
        "services/ringover/tests/runner.py", "Ringover Service")
  elif args.service == "agent":
    success = run_test_suite("services/agent/tests/runner.py", "Agent Service")
  elif args.service == "api":
    success = run_test_suite("api/tests/runner.py", "API")
  else:
    success = asyncio.run(run_all_tests())

  sys.exit(0 if success else 1)
