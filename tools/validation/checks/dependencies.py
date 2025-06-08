"""
Dependencies validation for the AI Voice Agent system.
"""

from typing import List
from ..utils.logger import ValidationLogger


class DependencyValidator:
  """Validates system dependencies."""

  def __init__(self, logger: ValidationLogger):
    self.logger = logger
    self.required_packages = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "sqlalchemy",
        "asyncpg",
        "redis",
        "httpx",
        "websockets",
        "openai",
        "anthropic",
        "google-generativeai",
        "python-jose",
        "python-multipart",
        "bcrypt",
        "passlib"
    ]

  def validate(self) -> bool:
    """Validate all required dependencies are installed."""
    print("\n📦 Validating Dependencies...")

    all_installed = True

    for package in self.required_packages:
      try:
        __import__(package.replace("-", "_"))
        self.logger.log_success(f"{package} is installed")
      except ImportError:
        self.logger.log_error(f"Missing required package: {package}")
        all_installed = False

    return all_installed
