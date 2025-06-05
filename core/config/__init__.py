"""
Configuration module for providers and application settings.
"""
from .app import SystemConfiguration, AgentConfiguration, ConfigurationManager
from .providers.telephony import (
    TelephonyProvider,
    TelephonyConfig,
    RingoverConfig
)
from .providers.ai import (
    LLMProvider,
    STTProvider,
    TTSProvider,
    LLMConfig,
    STTConfig,
    TTSConfig
)

__all__ = [
    # Main configuration
    "SystemConfiguration",
    "AgentConfiguration",
    "ConfigurationManager",

    # Telephony
    "TelephonyProvider",
    "TelephonyConfig",
    "RingoverConfig",

    # AI Services
    "LLMProvider",
    "STTProvider",
    "TTSProvider",
    "LLMConfig",
    "STTConfig",
    "TTSConfig"
]
