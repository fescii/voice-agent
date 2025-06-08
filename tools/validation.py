#!/usr/bin/env python3
"""
Comprehensive validation tool for the AI Voice Agent system - thin wrapper for backward compatibility.
"""
from .validation.main import SystemValidator
import sys


def main():
  """Main validation function."""
  validator = SystemValidator()
  success = validator.run_validation()
  return 0 if success else 1


if __name__ == "__main__":
  sys.exit(main())
