"""
Main application configuration module.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from core.config.registry import config_registry


@dataclass
class AppConfig:
  """Main application configuration."""
  name: str = "AI Voice Agent System"
  version: str = "1.0.0"
  environment: str = "development"
  debug: bool = True
  host: str = "localhost"
  port: int = 8000
  workers: int = 1


@dataclass
class AgentConfiguration:
  """Individual agent configuration."""
  agent_id: str
  name: str
  description: str
  max_concurrent_calls: int = 3
  script_names: List[str] = field(default_factory=list)
  personality: Dict[str, Any] = field(default_factory=dict)

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "agent_id": self.agent_id,
        "name": self.name,
        "description": self.description,
        "max_concurrent_calls": self.max_concurrent_calls,
        "script_names": self.script_names,
        "personality": self.personality
    }


@dataclass
class SystemConfiguration:
  """System-wide configuration."""
  # Agents
  agents: List[AgentConfiguration] = field(default_factory=list)

  # System limits
  max_total_concurrent_calls: int = 100
  max_agents: int = 5

  # Database
  database_url: str = "sqlite:///voice_agents.db"
  redis_url: str = "redis://localhost:6379"

  # Logging
  log_level: str = "INFO"
  log_file: Optional[str] = None

  # WebSocket
  websocket_host: str = "0.0.0.0"
  websocket_port: int = 8001

  # API
  api_host: str = "0.0.0.0"
  api_port: int = 8000

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "agents": [agent.to_dict() for agent in self.agents],
        "max_total_concurrent_calls": self.max_total_concurrent_calls,
        "max_agents": self.max_agents,
        "database_url": self.database_url,
        "redis_url": self.redis_url,
        "log_level": self.log_level,
        "log_file": self.log_file,
        "websocket_host": self.websocket_host,
        "websocket_port": self.websocket_port,
        "api_host": self.api_host,
        "api_port": self.api_port
    }


class ConfigurationManager:
  """Configuration manager for the voice agent system."""

  def __init__(self):
    """Initialize configuration manager."""
    self._config: Optional[SystemConfiguration] = None

  def load_from_env(self) -> SystemConfiguration:
    """
    Load configuration from environment variables.

    Returns:
        SystemConfiguration: The loaded configuration
    """
    import os

    # Create system configuration from environment
    config = SystemConfiguration(
        max_total_concurrent_calls=int(
            os.getenv("MAX_TOTAL_CONCURRENT_CALLS", "100")),
        max_agents=int(os.getenv("MAX_AGENTS", "5")),
        database_url=os.getenv("DATABASE_URL", "sqlite:///voice_agents.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_file=os.getenv("LOG_FILE"),
        websocket_host=os.getenv("WEBSOCKET_HOST", "0.0.0.0"),
        websocket_port=int(os.getenv("WEBSOCKET_PORT", "8001")),
        api_host=os.getenv("API_HOST", "0.0.0.0"),
        api_port=int(os.getenv("API_PORT", "8000"))
    )

    self._config = config
    return config

  def get_configuration(self) -> SystemConfiguration:
    """
    Get the current configuration.

    Returns:
        SystemConfiguration: The current configuration
    """
    if not self._config:
      return self.load_from_env()
    return self._config


def get_app_config() -> AppConfig:
  """
  Get application configuration from registry.

  Returns:
      AppConfig: Application configuration
  """
  # Get from environment or use defaults
  import os

  return AppConfig(
      name=os.getenv("APP_NAME", "AI Voice Agent System"),
      version=os.getenv("APP_VERSION", "1.0.0"),
      environment=os.getenv("ENVIRONMENT", "development"),
      debug=os.getenv("DEBUG", "true").lower() == "true",
      host=os.getenv("HOST", "localhost"),
      port=int(os.getenv("PORT", "8000")),
      workers=int(os.getenv("WORKERS", "1"))
  )
