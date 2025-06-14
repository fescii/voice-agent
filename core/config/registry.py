"""
Centralized configuration registry for the application.
All configurations are initialized once and accessed through this registry.
"""

from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

from .providers.ringover import RingoverConfig
from .providers.ai import LLMConfig, STTConfig, TTSConfig, LLMProvider, STTProvider, TTSProvider
from .providers.database import DatabaseConfig
from .providers.redis import RedisConfig
from .providers.security import SecurityConfig
from .providers.agent import AgentConfig
from .websocket import WebSocketConfig


class ConfigRegistry:
  """
  Centralized configuration registry.
  Initializes all configurations once and provides access throughout the application.
  """

  _instance: Optional['ConfigRegistry'] = None
  _initialized: bool = False

  def __new__(cls) -> 'ConfigRegistry':
    if cls._instance is None:
      cls._instance = super().__new__(cls)
    return cls._instance

  def __init__(self):
    # Don't auto-initialize - wait for explicit initialize() call
    if not hasattr(self, '_configs'):
      self._configs = {}

  def initialize(self):
    """Initialize all configurations. Should be called once during app startup."""
    if not self._initialized:
      # Load environment variables once
      load_dotenv()

      # Initialize all configurations
      self._configs = {
          'ringover': RingoverConfig(),
          'database': DatabaseConfig(),
          'redis': RedisConfig(),
          'security': SecurityConfig(),
          'agent': AgentConfig(),
          'llm': self._create_llm_config(),
          'stt': self._create_stt_config(),
          'tts': self._create_tts_config(),
          'websocket': self._create_websocket_config(),
      }

      ConfigRegistry._initialized = True

  @property
  def ringover(self) -> RingoverConfig:
    """Get Ringover configuration"""
    return self._configs['ringover']

  @property
  def database(self) -> DatabaseConfig:
    """Get database configuration"""
    return self._configs['database']

  @property
  def redis(self) -> RedisConfig:
    """Get Redis configuration"""
    return self._configs['redis']

  @property
  def llm(self) -> LLMConfig:
    """Get LLM configuration"""
    return self._configs['llm']

  @property
  def stt(self) -> STTConfig:
    """Get STT configuration"""
    return self._configs['stt']

  @property
  def tts(self) -> TTSConfig:
    """Get TTS configuration"""
    return self._configs['tts']

  @property
  def websocket(self) -> WebSocketConfig:
    """Get WebSocket configuration"""
    return self._configs['websocket']

  @property
  def security(self) -> SecurityConfig:
    """Get Security configuration"""
    return self._configs['security']

  @property
  def agent(self) -> AgentConfig:
    """Get Agent configuration"""
    return self._configs['agent']

  def get_config(self, name: str) -> Any:
    """Get configuration by name"""
    return self._configs.get(name)

  def get_all_configs(self) -> Dict[str, Any]:
    """Get all configurations"""
    return self._configs.copy()

  def reload(self):
    """Reload all configurations"""
    load_dotenv(override=True)
    for config in self._configs.values():
      if hasattr(config, 'reload'):
        config.reload()

  def _create_llm_config(self) -> LLMConfig:
    """Create LLM configuration from environment variables"""
    provider_str = os.getenv("LLM_PROVIDER", "openai").lower()
    provider = LLMProvider.OPENAI  # default

    if provider_str == "anthropic":
      provider = LLMProvider.ANTHROPIC
    elif provider_str == "google":
      provider = LLMProvider.GOOGLE
    elif provider_str == "custom":
      provider = LLMProvider.CUSTOM

    # Choose API key based on provider
    api_key = ""
    if provider == LLMProvider.OPENAI:
      api_key = os.getenv("OPENAI_API_KEY", "")
    elif provider == LLMProvider.ANTHROPIC:
      api_key = os.getenv("ANTHROPIC_API_KEY", "")
    elif provider == LLMProvider.GOOGLE:
      api_key = os.getenv("GOOGLE_API_KEY", "")
    else:
      api_key = os.getenv("LLM_API_KEY", "")

    return LLMConfig(
        provider=provider,
        api_key=api_key,
        model=os.getenv(
            "OPENAI_MODEL", "gpt-4") if provider == LLMProvider.OPENAI else os.getenv("LLM_MODEL", "gpt-4"),
        base_url=os.getenv(
            "OPENAI_BASE_URL") if provider == LLMProvider.OPENAI else os.getenv("LLM_BASE_URL"),
        max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")) if provider == LLMProvider.OPENAI else int(
            os.getenv("LLM_MAX_TOKENS", "1000")),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")) if provider == LLMProvider.OPENAI else float(
            os.getenv("LLM_TEMPERATURE", "0.7")),
        stream=os.getenv("LLM_STREAM", "true").lower() == "true"
    )

  def _create_stt_config(self) -> STTConfig:
    """Create STT configuration from environment variables"""
    provider_str = os.getenv("STT_PROVIDER", "whisper").lower()
    provider = STTProvider.WHISPER  # default

    if provider_str == "google":
      provider = STTProvider.GOOGLE
    elif provider_str == "azure":
      provider = STTProvider.AZURE
    elif provider_str == "custom":
      provider = STTProvider.CUSTOM

    # Choose API key based on provider
    api_key = ""
    if provider == STTProvider.WHISPER:
      api_key = os.getenv("WHISPER_API_KEY", "")
    elif provider == STTProvider.GOOGLE:
      api_key = os.getenv("GOOGLE_STT_API_KEY", "")
    elif provider == STTProvider.AZURE:
      api_key = os.getenv("AZURE_STT_API_KEY", "")
    else:
      api_key = os.getenv("STT_API_KEY", "")

    return STTConfig(
        provider=provider,
        api_key=api_key,
        language=os.getenv("STT_LANGUAGE", "en-US"),
        model=os.getenv(
            "WHISPER_MODEL", "whisper-1") if provider == STTProvider.WHISPER else os.getenv("STT_MODEL", "whisper-1")
    )

  def _create_tts_config(self) -> TTSConfig:
    """Create TTS configuration from environment variables"""
    provider_str = os.getenv("TTS_PROVIDER", "elevenlabs").lower()
    provider = TTSProvider.ELEVENLABS  # default

    if provider_str == "openai":
      provider = TTSProvider.OPENAI
    elif provider_str == "google":
      provider = TTSProvider.GOOGLE
    elif provider_str == "azure":
      provider = TTSProvider.AZURE
    elif provider_str == "custom":
      provider = TTSProvider.CUSTOM

    # Choose API key based on provider
    api_key = ""
    if provider == TTSProvider.ELEVENLABS:
      api_key = os.getenv("ELEVENLABS_API_KEY", "")
    elif provider == TTSProvider.OPENAI:
      api_key = os.getenv("OPENAI_TTS_API_KEY", "")
    elif provider == TTSProvider.GOOGLE:
      api_key = os.getenv("GOOGLE_TTS_API_KEY", "")
    elif provider == TTSProvider.AZURE:
      api_key = os.getenv("AZURE_TTS_API_KEY", "")
    else:
      api_key = os.getenv("TTS_API_KEY", "")

    return TTSConfig(
        provider=provider,
        api_key=api_key,
        voice_id=os.getenv("TTS_VOICE_ID", "default"),
        model=os.getenv("TTS_MODEL", "tts-1")
    )

  def _create_websocket_config(self) -> WebSocketConfig:
    """Create WebSocket configuration from environment variables"""
    return WebSocketConfig(
        host=os.getenv("WEBSOCKET_HOST", "0.0.0.0"),
        port=int(os.getenv("WEBSOCKET_PORT", "8080")),
        max_connections=int(os.getenv("WEBSOCKET_MAX_CONNECTIONS", "1000")),
        ping_interval=int(os.getenv("WEBSOCKET_PING_INTERVAL", "20")),
        ping_timeout=int(os.getenv("WEBSOCKET_PING_TIMEOUT", "10")),
        max_message_size=int(
            os.getenv("WEBSOCKET_MAX_MESSAGE_SIZE", "1048576")),
        require_auth=os.getenv("WEBSOCKET_REQUIRE_AUTH",
                               "true").lower() == "true",
        allowed_origins=self._parse_origins(
            os.getenv("WEBSOCKET_ALLOWED_ORIGINS", "*"))
    )

  def _parse_origins(self, origins_str: str) -> list:
    """Parse allowed origins from environment variable."""
    if origins_str == "*":
      return ["*"]
    return [origin.strip() for origin in origins_str.split(",") if origin.strip()]


# Global configuration registry instance - initialized in main.py
config_registry = ConfigRegistry()
