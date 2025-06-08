"""
Core logging functionality for validation system.
"""
from typing import List


class ValidationLogger:
  """Handles validation logging and tracking."""

  def __init__(self):
    self.errors: List[str] = []
    self.warnings: List[str] = []
    self.info: List[str] = []

  def log_error(self, message: str):
    """Log an error."""
    self.errors.append(f"ERROR: {message}")
    print(f"❌ {message}")

  def log_warning(self, message: str):
    """Log a warning."""
    self.warnings.append(f"WARNING: {message}")
    print(f"⚠️  {message}")

  def log_info(self, message: str):
    """Log info."""
    self.info.append(f"INFO: {message}")
    print(f"ℹ️  {message}")

  def log_success(self, message: str):
    """Log success."""
    print(f"✅ {message}")

  def print_summary(self, all_passed: bool):
    """Print validation summary."""
    print("\n" + "=" * 50)
    print("📊 Validation Summary")
    print("=" * 50)

    if all_passed:
      print("🎉 All validations passed!")
    else:
      print("💥 Some validations failed!")

    print(f"Errors: {len(self.errors)}")
    print(f"Warnings: {len(self.warnings)}")
    print(f"Info: {len(self.info)}")

    if self.errors:
      print("\n❌ Errors:")
      for error in self.errors:
        print(f"  {error}")

    if self.warnings:
      print("\n⚠️  Warnings:")
      for warning in self.warnings:
        print(f"  {warning}")
