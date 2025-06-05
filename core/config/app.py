"""
Application configuration management.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import os
from pathlib import Path

from .providers.telephony import TelephonyConfig, RingoverConfig, TelephonyProvider
from .providers.ai import LLMConfig, STTConfig, TTSConfig, LLMProvider, STTProvider, TTSProvider


@dataclass
class AgentConfiguration:
  """Individual agent configuration."""
  agent_id: str
  name: str
  description: str
  max_concurrent_calls: int = 3
  llm_config: Optional[LLMConfig] = None
  stt_config: Optional[STTConfig] = None
  tts_config: Optional[TTSConfig] = None
  script_names: List[str] = field(default_factory=list)
  personality: Dict[str, Any] = field(default_factory=dict)

  def to_dict(self) -> Dict[str, Any]:
    """Convert to dictionary."""
    return {
        "agent_id": self.agent_id,
        "name": self.name,
        "description": self.description,
        "max_concurrent_calls": self.max_concurrent_calls,
        "llm_config": self.llm_config.to_dict() if self.llm_config else None,
        "stt_config": self.stt_config.to_dict() if self.stt_config else None,
        "tts_config": self.tts_config.to_dict() if self.tts_config else None,
        "script_names": self.script_names,
        "personality": self.personality
    }


@dataclass
class SystemConfiguration:
  """System-wide configuration."""
  # Telephony
  telephony_config: TelephonyConfig

  # Agents
  agents: List[AgentConfiguration] = field(default_factory=list)

  # Default AI configs (can be overridden per agent)
  default_llm_config: Optional[LLMConfig] = None
  default_stt_config: Optional[STTConfig] = None
  default_tts_config: Optional[TTSConfig] = None

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
        "telephony_config": self.telephony_config.to_dict(),
        "agents": [agent.to_dict() for agent in self.agents],
        "default_llm_config": self.default_llm_config.to_dict() if self.default_llm_config else None,
        "default_stt_config": self.default_stt_config.to_dict() if self.default_stt_config else None,
        "default_tts_config": self.default_tts_config.to_dict() if self.default_tts_config else None,
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

  def __init__(self, config_path: Optional[Path] = None):
    """Initialize configuration manager."""
    self.config_path = config_path or Path("config/system.json")
    self._config: Optional[SystemConfiguration] = None

  def load_from_env(self) -> SystemConfiguration:
    """Load configuration from environment variables."""
    # Create Ringover config from env
    telephony_config = RingoverConfig(
        provider=TelephonyProvider.RINGOVER,
        api_key=os.getenv("RINGOVER_API_KEY", ""),
        api_secret=os.getenv("RINGOVER_API_SECRET"),
        webhook_secret=os.getenv("RINGOVER_WEBHOOK_SECRET"),
        max_channels_per_agent=int(os.getenv("RINGOVER_MAX_CHANNELS", "20")),
        concurrent_calls_limit=int(
            os.getenv("RINGOVER_CONCURRENT_LIMIT", "100"))
    )

    # Create default AI configs
    default_llm = LLMConfig(
        provider=LLMProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", "gpt-4"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
    )

    default_stt = STTConfig(
        provider=STTProvider.WHISPER,
        api_key=os.getenv("WHISPER_API_KEY", ""),
        language=os.getenv("STT_LANGUAGE", "en-US")
    )

    default_tts = TTSConfig(
        provider=TTSProvider.ELEVENLABS,
        api_key=os.getenv("ELEVENLABS_API_KEY", ""),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID")
    )

    return SystemConfiguration(
        telephony_config=telephony_config,
        default_llm_config=default_llm,
        default_stt_config=default_stt,
        default_tts_config=default_tts,
        database_url=os.getenv("DATABASE_URL", "sqlite:///voice_agents.db"),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        log_level=os.getenv("LOG_LEVEL", "INFO")
    )

  def get_configuration(self) -> SystemConfiguration:
    """Get the current configuration."""
    if self._config is None:
      self._config = self.load_from_env()
    return self._config
