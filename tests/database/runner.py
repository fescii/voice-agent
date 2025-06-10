"""
Database tests runner.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
  # Run authentication tests
  print("🚀 Running Authentication Tests...")
  exit_code = pytest.main([
      str(Path(__file__).parent / "test_auth.py"),
      "-v",
      "--tb=short"
  ])

  if exit_code == 0:
    print("✅ Authentication tests PASSED")
  else:
    print("❌ Authentication tests FAILED")

  sys.exit(exit_code)
