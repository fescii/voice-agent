"""
Logging configuration factory.
Creates logging configurations for different environments.
"""
import logging.config
from pathlib import Path
from typing import Dict, Any


class LoggingConfigFactory:
  """Factory for creating logging configurations."""

  @staticmethod
  def create_config(log_level: str = "INFO", log_dir: str = "/tmp/voice_agent_logs") -> Dict[str, Any]:
    """Create logging configuration."""

    # Create logs directory outside project directory to avoid reload conflicts
    logs_dir = Path(log_dir)
    logs_dir.mkdir(exist_ok=True, parents=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,            "formatters": {
                "detailed": {
                    "()": "core.logging.format.CustomFormatter",
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
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": str(logs_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(logs_dir / "error.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "core": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "services": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "api": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "data": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "models": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "wss": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            }
        },
        "root": {
            "level": log_level,
            "handlers": ["console", "file", "error_file"]
        }
    }
