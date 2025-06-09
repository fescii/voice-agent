"""
Logging setup and configuration
"""
import logging
from .config.initializer import LoggingInitializer


def setup_logging(log_level: str = "INFO") -> None:
  """Setup application logging configuration"""
  LoggingInitializer.initialize(log_level)


def get_logger(name: str) -> logging.Logger:
  """Get a logger instance for the given name"""
  return logging.getLogger(name)
