"""
OpenAI LLM provider implementation.
"""
import openai
from typing import List, Dict, Any, AsyncIterator
import asyncio

from .base import BaseLLMProvider
from ....models.external.llm.request import LLMRequest, LLMMessage
from ....models.external.llm.response import LLMResponse, LLMChoice, LLMUsage
from ....core.config.services.llm.openai import OpenAIConfig
from ....core.logging import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
  """OpenAI LLM provider."""

  def __init__(self, config: Dict[str, Any] = None):
    if config is None:
      config = OpenAIConfig().dict()
    super().__init__(config)

    # Initialize OpenAI client
    openai.api_key = self.config.get("api_key")
    if self.config.get("organization"):
      openai.organization = self.config.get("organization")

  async def generate_response(self, request: LLMRequest) -> LLMResponse:
    """Generate response using OpenAI API."""
    try:
      # Prepare messages
      messages = [
          {"role": msg.role, "content": msg.content}
          for msg in request.messages
      ]

      # Make API call
      response = await asyncio.to_thread(
          openai.ChatCompletion.create,
          model=request.model,
          messages=messages,
          temperature=request.temperature,
          max_tokens=request.max_tokens,
          stop=request.stop_sequences,
          **request.extra_params
      )

      # Parse response
      choices = []
      for choice in response.choices:
        choices.append(LLMChoice(
            message=choice.message.to_dict(),
            finish_reason=choice.finish_reason,
            index=choice.index
        ))

      usage = None
      if hasattr(response, 'usage'):
        usage = LLMUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )

      return LLMResponse(
          id=response.id,
          provider="openai",
          model=response.model,
          choices=choices,
          usage=usage,
          raw_response=response.to_dict()
      )

    except Exception as e:
      logger.error(f"OpenAI API error: {e}")
      raise

  async def stream_response(self, request: LLMRequest) -> AsyncIterator[str]:
    """Stream response from OpenAI API."""
    try:
      # Prepare messages
      messages = [
          {"role": msg.role, "content": msg.content}
          for msg in request.messages
      ]

      # Create streaming request
      stream = await asyncio.to_thread(
          openai.ChatCompletion.create,
          model=request.model,
          messages=messages,
          temperature=request.temperature,
          max_tokens=request.max_tokens,
          stop=request.stop_sequences,
          stream=True,
          **request.extra_params
      )

      # Yield tokens as they arrive
      for chunk in stream:
        if hasattr(chunk.choices[0].delta, 'content'):
          content = chunk.choices[0].delta.content
          if content:
            yield content

    except Exception as e:
      logger.error(f"OpenAI streaming error: {e}")
      raise

  async def validate_config(self) -> bool:
    """Validate OpenAI configuration."""
    try:
      # Test with a simple request
      test_response = await asyncio.to_thread(
          openai.ChatCompletion.create,
          model="gpt-3.5-turbo",
          messages=[{"role": "user", "content": "test"}],
          max_tokens=1
      )
      return True

    except Exception as e:
      logger.error(f"OpenAI config validation failed: {e}")
      return False
