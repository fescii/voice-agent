"""
Logging utilities for validation system.
"""

from typing import List


class ValidationLogger:
  """Handles logging for validation processes."""

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

  def get_summary(self) -> dict:
    """Get summary of logged messages."""
    return {
        "errors": len(self.errors),
        "warnings": len(self.warnings),
        "info": len(self.info)
    }

  def has_errors(self) -> bool:
    """Check if any errors were logged."""
    return len(self.errors) > 0
