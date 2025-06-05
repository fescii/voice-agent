"""
Base LLM provider interface.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from models.external.llm.request import LLMRequest
from models.external.llm.response import LLMResponse


class BaseLLMProvider(ABC):
  """Base class for all LLM providers."""

  def __init__(self, config: Dict[str, Any]):
    self.config = config

  @abstractmethod
  async def generate_response(
      self,
      request: LLMRequest
  ) -> LLMResponse:
    """
    Generate a response from the LLM.

    Args:
        request: LLM request object

    Returns:
        LLM response object
    """
    pass

  @abstractmethod
  async def stream_response(
      self,
      request: LLMRequest
  ) -> AsyncIterator[str]:
    """
    Stream response tokens from the LLM.

    Args:
        request: LLM request object

    Yields:
        Response tokens as they are generated
    """
    pass

  @abstractmethod
  async def validate_config(self) -> bool:
    """
    Validate provider configuration.

    Returns:
        True if configuration is valid
    """
    pass

  def get_provider_name(self) -> str:
    """Get the provider name."""
    return self.__class__.__name__.replace("Provider", "").lower()

  def prepare_messages(
      self,
      system_prompt: str,
      conversation_history: List[Dict[str, str]]
  ) -> List[Dict[str, str]]:
    """
    Prepare messages in the format expected by the provider.

    Args:
        system_prompt: System instruction
        conversation_history: List of conversation messages

    Returns:
        Formatted messages for the provider
    """
    messages = []

    if system_prompt:
      messages.append({"role": "system", "content": system_prompt})

    for message in conversation_history:
      messages.append(message)

    return messages
