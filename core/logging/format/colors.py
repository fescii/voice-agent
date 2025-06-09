"""
Color codes for log formatting.
"""


class LogColors:
  """ANSI color codes for log formatting."""

  DEBUG = '\033[36m'     # Cyan
  INFO = '\033[32m'      # Green
  WARNING = '\033[33m'   # Yellow
  ERROR = '\033[31m'     # Red
  CRITICAL = '\033[35m'  # Magenta
  RESET = '\033[0m'      # Reset

  @classmethod
  def get_color(cls, level_name: str) -> str:
    """Get color for log level."""
    return getattr(cls, level_name, cls.RESET)
