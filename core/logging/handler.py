"""
Custom log handlers
"""
import logging
from typing import Optional


class CallContextHandler(logging.Handler):
  """Handler that adds call context to log records"""

  def __init__(self, base_handler: logging.Handler):
    super().__init__()
    self.base_handler = base_handler

  def emit(self, record):
    """Emit log record with call context if available"""
    # Add call context from thread local storage if available
    try:
      from contextvars import ContextVar
      call_context: ContextVar[Optional[str]] = ContextVar(
          'call_context', default=None)
      call_id = call_context.get()
      if call_id:
        record.call_id = call_id
    except:
      pass

    self.base_handler.emit(record)
