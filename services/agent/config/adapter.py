"""
Agent configuration adapter between app config and database model.
"""
from typing import Dict, Any, Optional, Union
from core.config.app import AgentConfiguration
from data.db.models.agentconfig import AgentConfig


class AgentConfigProxy:
  """Proxy object that provides AgentConfig-like interface for app config."""

  def __init__(self, app_config: AgentConfiguration):
    """Initialize proxy with app configuration."""
    self.app_config = app_config

    # Build configuration dict
    self._config = {
        "personality": app_config.personality,
        "script_names": app_config.script_names,
        "llm_config": app_config.llm_config.to_dict() if app_config.llm_config else {},
        "stt_config": app_config.stt_config.to_dict() if app_config.stt_config else {},
        "tts_config": app_config.tts_config.to_dict() if app_config.tts_config else {}
    }

  @property
  def agent_id(self) -> str:
    return self.app_config.agent_id

  @property
  def name(self) -> str:
    return self.app_config.name

  @property
  def description(self) -> str:
    return self.app_config.description

  @property
  def max_concurrent_calls(self) -> int:
    return self.app_config.max_concurrent_calls

  @property
  def config(self) -> Dict[str, Any]:
    """Return the configuration dictionary."""
    return self._config

  @property
  def persona_prompt(self) -> str:
    """Build persona prompt from personality config."""
    return _build_persona_prompt(self.app_config.personality)

  @property
  def is_active(self) -> bool:
    return True

  @property
  def llm_provider(self) -> str:
    return self.app_config.llm_config.provider.value if self.app_config.llm_config else "openai"

  @property
  def llm_model(self) -> str:
    return self.app_config.llm_config.model if self.app_config.llm_config else "gpt-4"

  @property
  def llm_temperature(self) -> float:
    return self.app_config.llm_config.temperature if self.app_config.llm_config else 0.7

  @property
  def llm_max_tokens(self) -> int:
    return self.app_config.llm_config.max_tokens if self.app_config.llm_config else 150


class AgentConfigurationAdapter:
  """Adapter to convert between AgentConfiguration and AgentConfig."""

  @staticmethod
  def from_app_config(app_config: AgentConfiguration) -> AgentConfigProxy:
    """
    Convert AgentConfiguration (app config) to AgentConfig-compatible proxy.

    Args:
        app_config: Application agent configuration

    Returns:
        Agent configuration proxy
    """
    return AgentConfigProxy(app_config)


def _build_persona_prompt(personality: Dict[str, Any]) -> str:
  """
  Build a persona prompt from personality configuration.

  Args:
      personality: Personality configuration dictionary

  Returns:
      Formatted persona prompt string
  """
  if not personality:
    return "You are a helpful AI assistant."

  prompt_parts = []

  # Role
  role = personality.get("role", "assistant")
  prompt_parts.append(f"You are a {role}.")

  # Personality traits
  traits = personality.get("traits", [])
  if traits:
    traits_str = ", ".join(traits)
    prompt_parts.append(f"Your personality is {traits_str}.")

  # Conversation style
  style = personality.get("style", "professional")
  prompt_parts.append(f"You communicate in a {style} manner.")

  # Knowledge base
  knowledge_base = personality.get("knowledge_base", [])
  if knowledge_base:
    kb_str = ", ".join(knowledge_base)
    prompt_parts.append(f"You have expertise in: {kb_str}.")

  # Capabilities
  capabilities = personality.get("capabilities", [])
  if capabilities:
    cap_str = ", ".join(capabilities)
    prompt_parts.append(f"You can help with: {cap_str}.")

  # Additional instructions
  instructions = personality.get("instructions", "")
  if instructions:
    prompt_parts.append(instructions)

  return " ".join(prompt_parts)
