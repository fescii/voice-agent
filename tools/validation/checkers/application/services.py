"""
Application validation checkers.
"""
import importlib
from pathlib import Path
from typing import List

from ...core.logger import ValidationLogger


class DatabaseModelChecker:
  """Validates database models."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root

  def validate(self) -> bool:
    """Validate database models."""
    print("\n🗄️  Validating Database Models...")

    try:
      import sys
      sys.path.insert(0, str(self.project_root))

      from data.db.models.calllog import CallLog
      self.logger.log_success("CallLog model imported")

      return True
    except Exception as e:
      self.logger.log_error(f"Database model validation failed: {str(e)}")
      return False


class ApiEndpointChecker:
  """Validates API endpoints."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root

  def validate(self) -> bool:
    """Validate API endpoints."""
    print("\n🔗 Validating API Endpoints...")

    try:
      import sys
      sys.path.insert(0, str(self.project_root))

      # Core API imports
      from api.v1.calls.route import router as calls_router
      self.logger.log_success("Calls API router imported")

      from api.v1.agents.route import router as agents_router
      self.logger.log_success("Agents API router imported")

      return True
    except Exception as e:
      self.logger.log_error(f"API endpoint validation failed: {str(e)}")
      return False


class ServiceChecker:
  """Validates services."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root

  def validate(self) -> bool:
    """Validate services."""
    print("\n⚙️  Validating Services...")

    try:
      import sys
      sys.path.insert(0, str(self.project_root))

      # LLM services
      from services.llm.orchestrator import LLMOrchestrator
      self.logger.log_success("LLM Orchestrator imported")

      # TTS Service
      from services.tts.elevenlabs import ElevenLabsService
      self.logger.log_success("ElevenLabs TTS service imported")

      # STT Service
      from services.stt.whisper import WhisperService
      self.logger.log_success("Whisper STT service imported")

      # Call services
      from services.call.management.supervisor import CallSupervisor
      self.logger.log_success("Call Supervisor imported")

      # Task queue
      from services.taskqueue.queue import TaskQueue
      self.logger.log_success("Task Queue imported")

      return True
    except Exception as e:
      self.logger.log_error(f"Service validation failed: {str(e)}")
      return False


class ImportChecker:
  """Validates import system."""

  def __init__(self, logger: ValidationLogger, project_root: Path):
    self.logger = logger
    self.project_root = project_root

  def validate(self) -> bool:
    """Validate critical imports."""
    print("\n📥 Validating Critical Imports...")

    critical_imports = [
        "core.config.registry",
        "services.llm.orchestrator",
        "services.call.management.supervisor",
        "data.db.connection",
        "data.redis.connection"
    ]

    all_imported = True

    for module_name in critical_imports:
      try:
        import sys
        sys.path.insert(0, str(self.project_root))
        importlib.import_module(module_name)
        self.logger.log_success(f"{module_name} imported successfully")
      except ImportError as e:
        self.logger.log_error(f"Failed to import {module_name}: {str(e)}")
        all_imported = False

    return all_imported
