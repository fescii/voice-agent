"""
Infrastructure validation checkers.
"""
import importlib
import subprocess
from pathlib import Path
from typing import List

from ...core.logger import ValidationLogger


class DependencyChecker:
  """Validates system dependencies."""

  def __init__(self, logger: ValidationLogger):
    self.logger = logger

  def validate(self) -> bool:
    """Validate all required dependencies are installed."""
    print("\n📦 Validating Dependencies...")

    required_packages = [
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

    # Map of package names to import names for special cases
    import_mapping = {
        "google-generativeai": "google.generativeai",
        "python-jose": "jose",
        "python-multipart": "multipart"
    }

    all_installed = True

    for package in required_packages:
      try:
        import_name = import_mapping.get(package, package.replace("-", "_"))
        __import__(import_name)
        self.logger.log_success(f"{package} is installed")
      except ImportError:
        self.logger.log_error(f"Missing required package: {package}")
        all_installed = False

    return all_installed


class FileStructureChecker:
  """Validates project file structure."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root

  def validate(self) -> bool:
    """Validate the project file structure."""
    print("\n📁 Validating File Structure...")

    required_files = [
        "main.py",
        "requirements.txt",
        "setup.sh",
        "validate.py",
        # Core config files
        "core/config/__init__.py",
        "core/config/app/main.py",
        "core/config/providers/database.py",
        "core/config/providers/redis.py",
        "core/config/providers/ringover.py",
        # API files
        "api/__init__.py",
        "api/v1/__init__.py",
        "api/v1/calls/route.py",
        "api/v1/agents/route.py",
    ]

    all_exist = True

    for required_file in required_files:
      file_path = self.project_root / required_file
      if file_path.exists():
        self.logger.log_success(f"{required_file} exists")
      else:
        self.logger.log_error(f"Missing required file: {required_file}")
        all_exist = False

    return all_exist


class EnvironmentChecker:
  """Validates environment configuration."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root

  def validate(self) -> bool:
    """Validate environment configuration."""
    print("\n🌍 Validating Environment...")

    env_file = self.project_root / ".env"
    if not env_file.exists():
      self.logger.log_warning(".env file not found - using defaults")

    try:
      # Import and initialize config registry
      import sys
      sys.path.insert(0, str(self.project_root))
      from core.config.registry import config_registry
      config_registry.initialize()
      self.logger.log_success("Config registry initialized")
    except Exception as e:
      self.logger.log_error(f"Failed to initialize config registry: {str(e)}")
      return False

    try:
      db_config = config_registry.database
      self.logger.log_success("Database configuration loaded")
    except Exception as e:
      self.logger.log_error(f"Failed to load database configuration: {str(e)}")
      return False

    try:
      redis_config = config_registry.redis
      self.logger.log_success("Redis configuration loaded")
    except Exception as e:
      self.logger.log_error(f"Failed to load Redis configuration: {str(e)}")
      return False

    return True
