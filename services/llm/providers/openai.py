"""OpenAI LLM provider implementation."""

import json
import uuid
from typing import Dict, Any, AsyncIterator, List, Optional
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from .base import BaseLLMProvider
from models.external.llm.request import LLMRequest
from models.external.llm.response import LLMResponse, LLMChoice, LLMMessage, LLMUsage
from core.logging.setup import get_logger

logger = get_logger(__name__)


class OpenAIProvider(BaseLLMProvider):
  """OpenAI LLM provider."""

  def __init__(self, config: Dict[str, Any]):
    super().__init__(config)
    self.logger = logger
    self.provider_name = "openai"

    # Initialize OpenAI client
    api_key = config.get("api_key")
    if not api_key:
      raise ValueError("OpenAI API key is required")

    self.client = AsyncOpenAI(
        api_key=api_key,
        timeout=config.get("timeout", 30.0),
        max_retries=config.get("max_retries", 3)
    )

    self.model = config.get("model", "gpt-4o-mini")
    self.temperature = config.get("temperature", 0.7)
    self.max_tokens = config.get("max_tokens", 1024)

    logger.info(f"Initialized OpenAI provider with model: {self.model}")

  async def generate_response(self, request: LLMRequest) -> LLMResponse:
    """Generate a response using OpenAI."""
    try:
      # Prepare messages in OpenAI format
      messages = self._prepare_openai_messages(request)

      # Prepare request parameters
      params = {
          "model": request.model or self.model,
          "messages": messages,
          "temperature": request.temperature if request.temperature is not None else self.temperature,
          "max_tokens": request.max_tokens or self.max_tokens,
      }

      # Add optional parameters from extra_params
      if "top_p" in request.extra_params:
        params["top_p"] = request.extra_params["top_p"]

      if request.stop_sequences:
        # OpenAI supports up to 4 stop sequences
        params["stop"] = request.stop_sequences[:4]

      if "frequency_penalty" in request.extra_params:
        params["frequency_penalty"] = request.extra_params["frequency_penalty"]

      if "presence_penalty" in request.extra_params:
        params["presence_penalty"] = request.extra_params["presence_penalty"]

      logger.debug(f"Sending request to OpenAI: model={params['model']}")

      # Make API call
      response: ChatCompletion = await self.client.chat.completions.create(**params)

      # Convert response to our format
      choices = []
      for choice in response.choices:
        llm_message = LLMMessage(
            role=choice.message.role,
            content=choice.message.content or ""
        )
        choices.append(LLMChoice(
            message=llm_message,
            finish_reason=choice.finish_reason,
            index=choice.index
        ))

      usage = None
      if response.usage:
        usage = LLMUsage(
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens
        )

      return LLMResponse(
          id=response.id,
          provider=self.provider_name,
          model=response.model,
          choices=choices,
          usage=usage,
          raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
      )

    except Exception as e:
      logger.error(f"Error in OpenAI generate_response: {str(e)}")
      raise Exception(f"OpenAI API error: {str(e)}")

  async def stream_response(self, request: LLMRequest) -> AsyncIterator[str]:
    """Stream response tokens from OpenAI."""
    try:
      # Prepare messages in OpenAI format
      messages = self._prepare_openai_messages(request)

      # Prepare request parameters
      params = {
          "model": request.model or self.model,
          "messages": messages,
          "temperature": request.temperature if request.temperature is not None else self.temperature,
          "max_tokens": request.max_tokens or self.max_tokens,
          "stream": True,
      }

      # Add optional parameters from extra_params
      if "top_p" in request.extra_params:
        params["top_p"] = request.extra_params["top_p"]

      if request.stop_sequences:
        params["stop"] = request.stop_sequences[:4]

      if "frequency_penalty" in request.extra_params:
        params["frequency_penalty"] = request.extra_params["frequency_penalty"]

      if "presence_penalty" in request.extra_params:
        params["presence_penalty"] = request.extra_params["presence_penalty"]

      logger.debug(f"Starting OpenAI stream: model={params['model']}")

      # Stream the response
      stream = await self.client.chat.completions.create(**params)
      async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
          yield chunk.choices[0].delta.content

    except Exception as e:
      logger.error(f"Error in OpenAI stream_response: {str(e)}")
      raise Exception(f"OpenAI streaming error: {str(e)}")

  async def validate_config(self) -> bool:
    """Validate OpenAI provider configuration."""
    try:
      # Test with a minimal request
      response = await self.client.chat.completions.create(
          model=self.model,
          messages=[{"role": "user", "content": "test"}],
          max_tokens=1
      )
      logger.info("OpenAI configuration validation successful")
      return True
    except Exception as e:
      logger.error(f"OpenAI configuration validation failed: {str(e)}")
      return False

  def _prepare_openai_messages(self, request: LLMRequest) -> List[Dict[str, str]]:
    """Convert LLMRequest messages to OpenAI format."""
    messages = []

    # Add system prompt if provided in extra_params
    if "system_prompt" in request.extra_params:
      messages.append({
          "role": "system",
          "content": request.extra_params["system_prompt"]
      })

    # Add conversation messages
    for message in request.messages:
      messages.append({
          "role": message.role,
          "content": message.content
      })

    return messages

  def get_available_models(self) -> List[str]:
    """Get list of available OpenAI models."""
    return [
        # GPT-4o Models (Latest)
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4o-2024-11-20",
        "gpt-4o-2024-08-06",
        "gpt-4o-2024-05-13",
        "gpt-4o-mini-2024-07-18",

        # GPT-4 Turbo Models
        "gpt-4-turbo",
        "gpt-4-turbo-2024-04-09",
        "gpt-4-turbo-preview",
        "gpt-4-0125-preview",
        "gpt-4-1106-preview",

        # GPT-4 Models
        "gpt-4",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-32k-0613",

        # GPT-3.5 Models
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-0125",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-instruct"
    ]
