"""
Logging setup and configuration
"""
import logging
import logging.config
import sys
from pathlib import Path

from core.logging.format import CustomFormatter


def setup_logging(log_level: str = "INFO") -> None:
  """Setup application logging configuration"""

  # Create logs directory if it doesn't exist
  logs_dir = Path("logs")
  logs_dir.mkdir(exist_ok=True)

  # Logging configuration
  logging_config = {
      "version": 1,
      "disable_existing_loggers": False,
      "formatters": {
          "detailed": {
              "()": CustomFormatter,
              "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
          },
          "simple": {
              "format": "%(levelname)s - %(message)s"
          }
      },
      "handlers": {
          "console": {
              "class": "logging.StreamHandler",
              "level": log_level,
              "formatter": "detailed",
              "stream": sys.stdout
          },
          "file": {
              "class": "logging.handlers.RotatingFileHandler",
              "level": log_level,
              "formatter": "detailed",
              "filename": logs_dir / "app.log",
              "maxBytes": 10485760,  # 10MB
              "backupCount": 5
          },
          "error_file": {
              "class": "logging.handlers.RotatingFileHandler",
              "level": "ERROR",
              "formatter": "detailed",
              "filename": logs_dir / "error.log",
              "maxBytes": 10485760,  # 10MB
              "backupCount": 5
          }
      },
      "loggers": {
          "": {  # Root logger
              "level": log_level,
              "handlers": ["console", "file", "error_file"],
              "propagate": False
          },
          "uvicorn": {
              "level": log_level,
              "handlers": ["console"],
              "propagate": False
          },
          "fastapi": {
              "level": log_level,
              "handlers": ["console", "file"],
              "propagate": False
          }
      }
  }

  logging.config.dictConfig(logging_config)

  # Log startup message
  logger = logging.getLogger(__name__)
  logger.info("Logging system initialized")


def get_logger(name: str) -> logging.Logger:
  """
  Get a logger instance with the given name

  Args:
      name: Logger name, typically __name__ from the calling module

  Returns:
      Configured logger instance
  """
  return logging.getLogger(name)
