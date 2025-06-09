"""
Log message formatters.
"""
import logging
from datetime import datetime
from .colors import LogColors


class BasicFormatter(logging.Formatter):
  """Basic log formatter with timestamp and colors."""

  def format(self, record):
    """Format log record with basic information."""
    record.asctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    color = LogColors.get_color(record.levelname)
    log_format = (
        f"{color}"
        f"[{record.asctime}] {record.levelname:8} | "
        f"{record.name} | {record.getMessage()}"
        f"{LogColors.RESET}"
    )

    return log_format


class CallAwareFormatter(logging.Formatter):
  """Formatter that includes call ID when available."""

  def format(self, record):
    """Format log record with call ID if present."""
    record.asctime = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    color = LogColors.get_color(record.levelname)

    if hasattr(record, 'call_id'):
      call_id = getattr(record, 'call_id', 'N/A')
      log_format = (
          f"{color}"
          f"[{record.asctime}] {record.levelname:8} | "
          f"CALL:{call_id} | {record.name} | {record.getMessage()}"
          f"{LogColors.RESET}"
      )
    else:
      log_format = (
          f"{color}"
          f"[{record.asctime}] {record.levelname:8} | "
          f"{record.name} | {record.getMessage()}"
          f"{LogColors.RESET}"
      )

    return log_format
