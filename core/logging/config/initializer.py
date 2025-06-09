"""
Logging initializer.
Handles the initialization of logging configuration.
"""
import logging.config
import os
from typing import Optional
from .factory import LoggingConfigFactory


class LoggingInitializer:
  """Initializes logging configuration for the application."""

  @staticmethod
  def initialize(log_level: Optional[str] = None, log_dir: Optional[str] = None) -> None:
    """Initialize logging configuration."""

    # Get configuration from environment or defaults
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    log_dir = log_dir or os.getenv("LOG_DIR", "/tmp/voice_agent_logs")

    # Create and apply logging configuration
    config = LoggingConfigFactory.create_config(log_level, log_dir)
    logging.config.dictConfig(config)

    # Log initialization success
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging initialized - Level: {log_level}, Directory: {log_dir}")
