"""
File structure validation for the AI Voice Agent system.
"""

from pathlib import Path
from typing import List
from ..utils.logger import ValidationLogger


class FileStructureValidator:
  """Validates project file structure."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root
    self.required_files = [
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
        "api/v1/webhooks/ringover/route.py",
        # Services
        "services/llm/orchestrator.py",
        "services/tts/elevenlabs.py",
        "services/stt/whisper.py",
        # Data layer
        "data/db/connection.py",
        "data/redis/connection.py",
        # WebSocket
        "wss/endpoint.py",
        "wss/handlers.py",
    ]

  def validate(self) -> bool:
    """Validate the project file structure."""
    print("\n📁 Validating File Structure...")

    missing_files = []

    for file_path in self.required_files:
      full_path = self.project_root / file_path
      if not full_path.exists():
        missing_files.append(file_path)
        self.logger.log_error(f"Missing required file: {file_path}")
      else:
        self.logger.log_success(f"Found: {file_path}")

    return len(missing_files) == 0
