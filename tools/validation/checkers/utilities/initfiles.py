"""
Utility functions for validation system.
"""
import os
from pathlib import Path
from typing import List

from ...core.logger import ValidationLogger


class InitFileCreator:
  """Creates missing __init__.py files."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root

  def create_missing_files(self) -> bool:
    """Create missing __init__.py files."""
    print("\n📝 Creating Missing __init__.py Files...")

    directories_to_check = [
        "api",
        "api/v1",
        "api/v1/calls",
        "api/v1/calls/actions",
        "api/v1/agents",
        "api/v1/agents/config",
        "api/v1/webhooks",
        "api/v1/webhooks/ringover",
        "api/v1/schemas",
        "api/v1/schemas/request",
        "api/v1/schemas/response",
        "core",
        "core/config",
        "core/config/app",
        "core/config/providers",
        "core/config/services",
        "core/config/services/llm",
        "core/config/services/tts",
        "core/config/services/stt",
        "core/config/services/notification",
        "core/logging",
        "core/security",
        "core/security/auth",
        "data",
        "data/db",
        "data/db/models",
        "data/db/ops",
        "data/redis",
        "data/redis/ops",
        "models",
        "models/external",
        "models/external/llm",
        "models/external/ringover",
        "models/internal",
        "services",
        "services/agent",
        "services/agent/conversation",
        "services/agent/config",
        "services/audio",
        "services/call",
        "services/call/management",
        "services/llm",
        "services/llm/providers",
        "services/llm/prompt",
        "services/llm/script",
        "services/notification",
        "services/notification/channels",
        "services/ringover",
        "services/stt",
        "services/taskqueue",
        "services/transcription",
        "services/tts",
        "wss",
        "wss/handlers"
    ]

    files_created = 0

    for directory in directories_to_check:
      dir_path = self.project_root / directory
      init_file = dir_path / "__init__.py"

      if dir_path.exists() and not init_file.exists():
        try:
          init_file.write_text("")
          self.logger.log_success(f"Created {directory}/__init__.py")
          files_created += 1
        except Exception as e:
          self.logger.log_error(
              f"Failed to create {directory}/__init__.py: {str(e)}")

    if files_created == 0:
      self.logger.log_success("All __init__.py files are present")

    return True
