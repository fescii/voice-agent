"""
Main system validator that coordinates all validation checks.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple, Callable

from .core import ValidationLogger
from .checkers import (
    DependencyChecker, FileStructureChecker, EnvironmentChecker,
    DatabaseModelChecker, ApiEndpointChecker, ServiceChecker, ImportChecker,
    InitFileCreator
)


class SystemValidator:
  """Comprehensive system validation coordinator."""

  def __init__(self):
    # Add project root to path
    self.project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(self.project_root))

    # Initialize logger and checkers
    self.logger = ValidationLogger()

    # Infrastructure checkers
    self.dependency_checker = DependencyChecker(self.logger)
    self.file_structure_checker = FileStructureChecker(
        self.logger, self.project_root)
    self.environment_checker = EnvironmentChecker(
        self.logger, self.project_root)

    # Application checkers
    self.database_checker = DatabaseModelChecker(
        self.logger, self.project_root)
    self.api_checker = ApiEndpointChecker(self.logger, self.project_root)
    self.service_checker = ServiceChecker(self.logger, self.project_root)
    self.import_checker = ImportChecker(self.logger, self.project_root)

    # Utilities
    self.init_file_creator = InitFileCreator(self.logger, self.project_root)

  def run_validation(self) -> bool:
    """Run complete validation."""
    print("🚀 Starting AI Voice Agent System Validation")
    print("=" * 50)

    # Create missing __init__.py files first
    self.init_file_creator.create_missing_files()

    validation_steps: List[Tuple[str, Callable[[], bool]]] = [
        ("Dependencies", self.dependency_checker.validate),
        ("File Structure", self.file_structure_checker.validate),
        ("Environment", self.environment_checker.validate),
        ("Database Models", self.database_checker.validate),
        ("API Endpoints", self.api_checker.validate),
        ("Services", self.service_checker.validate),
        ("Imports", self.import_checker.validate),
    ]

    all_passed = True

    for step_name, step_func in validation_steps:
      try:
        if not step_func():
          all_passed = False
      except Exception as e:
        self.logger.log_error(
            f"Validation step '{step_name}' failed with exception: {str(e)}")
        all_passed = False

    # Print summary
    self.logger.print_summary(all_passed)
    return all_passed

  @property
  def errors(self) -> List[str]:
    """Get validation errors."""
    return self.logger.errors

  @property
  def warnings(self) -> List[str]:
    """Get validation warnings."""
    return self.logger.warnings

  @property
  def info(self) -> List[str]:
    """Get validation info."""
    return self.logger.info
