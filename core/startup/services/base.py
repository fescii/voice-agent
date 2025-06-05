"""
Base startup service interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
  from core.startup.manager import StartupContext


class BaseStartupService(ABC):
  """Base class for all startup services."""

  def __init__(self, name: str, is_critical: bool = True):
    self.name = name
    self.is_critical = is_critical

  @abstractmethod
  async def initialize(self, context: "StartupContext") -> Dict[str, Any]:
    """
    Initialize the service.

    Args:
        context: Startup context containing configuration and other services

    Returns:
        Dict containing service metadata

    Raises:
        Exception: If initialization fails
    """
    pass

  async def cleanup(self, context: "StartupContext") -> None:
    """
    Cleanup service resources.

    Args:
        context: Startup context
    """
    pass

  def get_health_check(self) -> Dict[str, Any]:
    """
    Get health check information for this service.

    Returns:
        Dict containing health status
    """
    return {
        "service": self.name,
        "status": "unknown",
        "critical": self.is_critical
    }
