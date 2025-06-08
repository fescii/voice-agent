"""
LLM orchestrator for managing multiple providers.
"""
from typing import Dict, Any, Optional, List, AsyncIterator
from enum import Enum

from services.llm.providers.base import BaseLLMProvider
from services.llm.providers.openai import OpenAIProvider
from services.llm.providers.gemini import GeminiProvider
from services.llm.providers.anthropic import AnthropicProvider
from models.external.llm.request import LLMRequest, LLMMessage
from models.external.llm.response import LLMResponse
from core.config.registry import config_registry
from core.logging import get_logger

logger = get_logger(__name__)


class LLMProviderType(Enum):
  """Supported LLM providers."""
  OPENAI = "openai"
  GEMINI = "gemini"
  ANTHROPIC = "anthropic"


class LLMOrchestrator:
  """Orchestrates LLM interactions across multiple providers."""

  def __init__(self):
    self.logger = logger
    self._providers: Dict[str, BaseLLMProvider] = {}
    self._initialize_providers()

  def _initialize_providers(self):
    """Initialize all available LLM providers."""
    # Get LLM config from centralized registry
    llm_config = config_registry.llm

    # Initialize OpenAI
    try:
      if llm_config.provider.value == 'openai':
        self._providers[LLMProviderType.OPENAI.value] = OpenAIProvider({
            'api_key': llm_config.api_key,
            'model': llm_config.model,
            'base_url': llm_config.base_url,
            'max_tokens': llm_config.max_tokens,
            'temperature': llm_config.temperature
        })
        self.logger.info("Initialized OpenAI provider")
    except Exception as e:
      self.logger.warning(f"Failed to initialize OpenAI provider: {e}")

    # Initialize Gemini
    try:
      if llm_config.provider.value == 'google':
        self._providers[LLMProviderType.GEMINI.value] = GeminiProvider({
            'api_key': llm_config.api_key,
            'model': llm_config.model,
            'max_tokens': llm_config.max_tokens,
            'temperature': llm_config.temperature
        })
        self.logger.info("Initialized Gemini provider")
    except Exception as e:
      self.logger.warning(f"Failed to initialize Gemini provider: {e}")

    # Initialize Anthropic
    try:
      if llm_config.provider.value == 'anthropic':
        self._providers[LLMProviderType.ANTHROPIC.value] = AnthropicProvider({
            'api_key': llm_config.api_key,
            'model': llm_config.model,
            'max_tokens': llm_config.max_tokens,
            'temperature': llm_config.temperature
        })
        self.logger.info("Initialized Anthropic provider")
    except Exception as e:
      self.logger.warning(f"Failed to initialize Anthropic provider: {e}")

    self.logger.info(
        f"Successfully initialized {len(self._providers)} LLM providers")

  async def generate_response(
      self,
      messages: List[Dict[str, str]],
      provider: str = "openai",
      model: str = "gpt-3.5-turbo",
      temperature: float = 0.7,
      max_tokens: int = 150,
      **kwargs
  ) -> Optional[LLMResponse]:
    """
    Generate response using specified provider.

    Args:
        messages: Conversation messages
        provider: Provider name
        model: Model name
        temperature: Response randomness
        max_tokens: Maximum tokens
        **kwargs: Additional parameters

    Returns:
        LLM response or None if failed
    """
    try:
      if provider not in self._providers:
        self.logger.error(f"Provider {provider} not available")
        return None

      # Convert messages to LLMMessage objects
      llm_messages = [
          LLMMessage(role=msg["role"], content=msg["content"])
          for msg in messages
      ]

      # Create request
      request = LLMRequest(
          messages=llm_messages,
          model=model,
          temperature=temperature,
          max_tokens=max_tokens,
          extra_params=kwargs
      )

      # Get provider and generate response
      llm_provider = self._providers[provider]
      response = await llm_provider.generate_response(request)

      self.logger.debug(f"Generated response using {provider}")
      return response

    except Exception as e:
      self.logger.error(f"Failed to generate LLM response: {e}")
      return None

  async def stream_response(
      self,
      messages: List[Dict[str, str]],
      provider: str = "openai",
      model: str = "gpt-3.5-turbo",
      temperature: float = 0.7,
      max_tokens: int = 150,
      **kwargs
  ) -> AsyncIterator[str]:
    """
    Stream response using specified provider.

    Args:
        messages: Conversation messages
        provider: Provider name
        model: Model name
        temperature: Response randomness
        max_tokens: Maximum tokens
        **kwargs: Additional parameters

    Yields:
        Response tokens
    """
    try:
      if provider not in self._providers:
        self.logger.error(f"Provider {provider} not available")
        return

      # Convert messages to LLMMessage objects
      llm_messages = [
          LLMMessage(role=msg["role"], content=msg["content"])
          for msg in messages
      ]

      # Create request
      request = LLMRequest(
          messages=llm_messages,
          model=model,
          temperature=temperature,
          max_tokens=max_tokens,
          stream=True,
          extra_params=kwargs
      )

      # Get provider and stream response
      llm_provider = self._providers[provider]
      async for token in await llm_provider.stream_response(request):
        yield token

    except Exception as e:
      self.logger.error(f"Failed to stream LLM response: {e}")

  def get_available_providers(self) -> List[str]:
    """Get list of available providers."""
    return list(self._providers.keys())

  async def validate_provider(self, provider: str) -> bool:
    """
    Validate provider configuration.

    Args:
        provider: Provider name

    Returns:
        True if provider is valid
    """
    try:
      if provider not in self._providers:
        return False

      return await self._providers[provider].validate_config()

    except Exception as e:
      self.logger.error(f"Provider validation failed for {provider}: {e}")
      return False
