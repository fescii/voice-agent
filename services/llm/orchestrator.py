"""
LLM orchestrator for managing multiple providers.
"""
from typing import Dict, Any, Optional, List, AsyncIterator
from enum import Enum

from .providers.base import BaseLLMProvider
from .providers.openai import OpenAIProvider
from .providers.gemini import GeminiProvider
from .providers.anthropic import AnthropicProvider
from ..models.external.llm.request import LLMRequest, LLMMessage
from ..models.external.llm.response import LLMResponse
from ..core.logging import get_logger

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
    try:
      # Initialize OpenAI
      self._providers[LLMProviderType.OPENAI.value] = OpenAIProvider()

      # Initialize Gemini
      # self._providers[LLMProviderType.GEMINI.value] = GeminiProvider()

      # Initialize Anthropic
      # self._providers[LLMProviderType.ANTHROPIC.value] = AnthropicProvider()

      self.logger.info(f"Initialized {len(self._providers)} LLM providers")

    except Exception as e:
      self.logger.error(f"Failed to initialize LLM providers: {e}")

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
      async for token in llm_provider.stream_response(request):
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
