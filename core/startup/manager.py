"""
Application startup context manager.
Handles initialization and cleanup of all system services.
"""
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone

from core.config.registry import config_registry
from core.logging.setup import get_logger

logger = get_logger(__name__)


@dataclass
class ServiceStatus:
  """Status of an individual service."""
  name: str
  status: str  # "initializing", "running", "error", "stopped"
  initialized_at: Optional[datetime] = None
  error_message: Optional[str] = None
  metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StartupContext:
  """Application startup context containing all initialized services."""
  configuration: Any
  services: Dict[str, ServiceStatus] = field(default_factory=dict)
  startup_time: datetime = field(
      default_factory=lambda: datetime.now(timezone.utc))

  def __post_init__(self):
    """Ensure startup_time is timezone-aware if not already set."""
    if self.startup_time.tzinfo is None:
      self.startup_time = self.startup_time.replace(tzinfo=timezone.utc)

  def add_service(self, name: str, status: str = "initializing",
                  metadata: Optional[Dict[str, Any]] = None) -> None:
    """Add a service to the context."""
    self.services[name] = ServiceStatus(
        name=name,
        status=status,
        metadata=metadata or {}
    )

  def mark_service_running(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Mark a service as running."""
    if name in self.services:
      self.services[name].status = "running"
      self.services[name].initialized_at = datetime.now(timezone.utc)
      if metadata:
        self.services[name].metadata.update(metadata)

  def mark_service_error(self, name: str, error: str) -> None:
    """Mark a service as having an error."""
    if name in self.services:
      self.services[name].status = "error"
      self.services[name].error_message = error

  def get_service_status(self, name: str) -> Optional[ServiceStatus]:
    """Get status of a specific service."""
    return self.services.get(name)

  def get_healthy_services(self) -> List[str]:
    """Get list of healthy (running) services."""
    return [name for name, status in self.services.items()
            if status.status == "running"]

  def get_failed_services(self) -> List[str]:
    """Get list of failed services."""
    return [name for name, status in self.services.items()
            if status.status == "error"]

  def get_failed_critical_services(self, service_registry: Dict[str, bool]) -> List[str]:
    """Get list of failed critical services."""
    return [name for name, status in self.services.items()
            if status.status == "error" and service_registry.get(name, True)]

  def is_healthy(self, service_registry: Optional[Dict[str, bool]] = None) -> bool:
    """Check if all critical services are healthy."""
    if service_registry is None:
      # Fallback to old behavior if no registry provided
      failed = self.get_failed_services()
      return len(failed) == 0

    failed_critical = self.get_failed_critical_services(service_registry)
    return len(failed_critical) == 0


class StartupManager:
  """Manages application startup and service initialization."""

  def __init__(self):
    self.context: Optional[StartupContext] = None
    # Use centralized config registry instead

  @asynccontextmanager
  async def startup_context(self):
    """Async context manager for application startup."""
    logger.info("🚀 Starting application initialization...")

    try:
      # Initialize startup context with explicit timezone-aware startup time
      startup_time = datetime.now(timezone.utc)
      self.context = StartupContext(
          configuration=config_registry,
          startup_time=startup_time
      )

      # Initialize all services
      await self._initialize_services()

      # Services have been initialized - critical failures would have raised exceptions already
      total_time = (datetime.now(timezone.utc) -
                    self.context.startup_time).total_seconds()
      logger.info(f"✅ Application startup completed in {total_time:.2f}s")

      yield self.context

    except Exception as e:
      logger.error(f"❌ Application startup failed: {e}")
      raise
    finally:
      # Cleanup
      if self.context:
        await self._cleanup_services()
        logger.info("🧹 Application cleanup completed")

  async def _initialize_services(self) -> None:
    """Initialize all application services in order."""
    # Ensure context is initialized
    if not self.context:
      raise RuntimeError("Startup context not initialized")

    from .services.database import DatabaseService
    from .services.redis import RedisService
    from .services.telephony import TelephonyService
    from .services.llm import LLMService
    from .services.audio import AudioService
    from .services.monitoring import MonitoringService
    from .services.ringover import RingoverService

    services = [
        DatabaseService(),
        RedisService(),
        TelephonyService(),
        LLMService(),
        AudioService(),
        MonitoringService(),
        RingoverService()
    ]

    for service in services:
      try:
        self.context.add_service(service.name)
        logger.info(f"⏳ Initializing {service.name}...")

        metadata = await service.initialize(self.context)
        self.context.mark_service_running(service.name, metadata)

        logger.info(f"✅ {service.name} initialized successfully")

      except Exception as e:
        error_msg = f"Failed to initialize {service.name}: {e}"
        logger.error(f"❌ {error_msg}")
        self.context.mark_service_error(service.name, str(e))

        # Fail immediately on any service failure
        raise RuntimeError(error_msg)

  async def _cleanup_services(self) -> None:
    """Cleanup all initialized services."""
    if not self.context:
      return

    # Import cleanup services
    from .services.database import DatabaseService
    from .services.redis import RedisService
    from .services.telephony import TelephonyService
    from .services.llm import LLMService
    from .services.audio import AudioService
    from .services.monitoring import MonitoringService
    from .services.ringover import RingoverService

    services = [
        RingoverService(),
        MonitoringService(),
        AudioService(),
        LLMService(),
        TelephonyService(),
        RedisService(),
        DatabaseService()
    ]

    for service in services:
      if service.name in self.context.services:
        try:
          logger.info(f"🧹 Cleaning up {service.name}...")
          await service.cleanup(self.context)
          self.context.services[service.name].status = "stopped"
        except Exception as e:
          logger.error(f"Error cleaning up {service.name}: {e}")
