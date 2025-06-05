"""
Anthropic LLM Provider Implementation
Handles Claude model interactions for the Voice Agent system.
"""

from typing import List, Dict, Any, Optional, AsyncGenerator
import anthropic
from anthropic.types import MessageParam, ContentBlock
from anthropic._types import NOT_GIVEN, NotGiven

from .base import BaseLLMProvider
from models.external.llm.request import LLMRequest, Message
from models.external.llm.response import LLMResponse, LLMStreamResponse
from core.config.services.llm.anthropic import AnthropicConfig
from core.logging import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
  """Anthropic Claude LLM Provider"""

  def __init__(self, config: AnthropicConfig):
    self.config = config
    self.client = anthropic.AsyncAnthropic(
        api_key=config.api_key,
        timeout=config.timeout
    )
    self.provider_name = "anthropic"
    logger.info(f"Initialized Anthropic provider with model: {config.model}")

  async def generate_response(
      self,
      request: LLMRequest,
      **kwargs
  ) -> LLMResponse:
    """Generate a response using Anthropic Claude"""
    try:
      # Convert messages to Anthropic format
      messages = self._convert_messages(request.messages)

      # Prepare request parameters
      params = {
          "model": self.config.model,
          "messages": messages,
          "max_tokens": request.max_tokens or self.config.max_tokens,
          "temperature": request.temperature or self.config.temperature,
      }

      # Add optional parameters
      if request.system_prompt:
        params["system"] = request.system_prompt

      if request.top_p is not None:
        params["top_p"] = request.top_p

      if request.stop_sequences:
        # Max 4 for Anthropic
        params["stop_sequences"] = request.stop_sequences[:4]

      logger.debug(f"Sending request to Anthropic: {params['model']}")

      # Make API call
      response = await self.client.messages.create(**params)

      # Extract response content
      content = ""
      if response.content:
        for block in response.content:
          if hasattr(block, 'text'):
            content += block.text

      # Calculate tokens (approximate for Anthropic)
      prompt_tokens = self._estimate_tokens(
          " ".join([msg.content for msg in request.messages]))
      completion_tokens = self._estimate_tokens(content)

      return LLMResponse(
          content=content,
          provider=self.provider_name,
          model=self.config.model,
          prompt_tokens=prompt_tokens,
          completion_tokens=completion_tokens,
          total_tokens=prompt_tokens + completion_tokens,
          finish_reason=response.stop_reason or "stop",
          metadata={
              "usage": {
                  "input_tokens": getattr(response.usage, 'input_tokens', prompt_tokens),
                  "output_tokens": getattr(response.usage, 'output_tokens', completion_tokens)
              },
              "model": response.model,
              "stop_reason": response.stop_reason
          }
      )

    except anthropic.APIError as e:
      logger.error(f"Anthropic API error: {str(e)}")
      raise Exception(f"Anthropic API error: {str(e)}")
    except Exception as e:
      logger.error(f"Unexpected error in Anthropic provider: {str(e)}")
      raise

  async def stream_response(
      self,
      request: LLMRequest,
      **kwargs
  ) -> AsyncGenerator[LLMStreamResponse, None]:
    """Stream response from Anthropic Claude"""
    try:
      # Convert messages to Anthropic format
      messages = self._convert_messages(request.messages)

      # Prepare request parameters
      params = {
          "model": self.config.model,
          "messages": messages,
          "max_tokens": request.max_tokens or self.config.max_tokens,
          "temperature": request.temperature or self.config.temperature,
          "stream": True,
      }

      # Add optional parameters
      if request.system_prompt:
        params["system"] = request.system_prompt

      if request.top_p is not None:
        params["top_p"] = request.top_p

      if request.stop_sequences:
        params["stop_sequences"] = request.stop_sequences[:4]

      logger.debug(f"Starting stream from Anthropic: {params['model']}")

      # Stream the response
      async with self.client.messages.stream(**params) as stream:
        async for event in stream:
          if hasattr(event, 'delta') and hasattr(event.delta, 'text'):
            yield LLMStreamResponse(
                content=event.delta.text,
                provider=self.provider_name,
                model=self.config.model,
                is_complete=False,
                metadata={
                    "event_type": event.type if hasattr(event, 'type') else "content_block_delta"
                }
            )

        # Send completion signal
        yield LLMStreamResponse(
            content="",
            provider=self.provider_name,
            model=self.config.model,
            is_complete=True,
            metadata={
                "event_type": "message_stop",
                "usage": {
                    "input_tokens": getattr(stream.get_final_message().usage, 'input_tokens', 0),
                    "output_tokens": getattr(stream.get_final_message().usage, 'output_tokens', 0)
                }
            }
        )

    except anthropic.APIError as e:
      logger.error(f"Anthropic streaming error: {str(e)}")
      yield LLMStreamResponse(
          content="",
          provider=self.provider_name,
          model=self.config.model,
          is_complete=True,
          error=str(e)
      )
    except Exception as e:
      logger.error(f"Unexpected streaming error: {str(e)}")
      yield LLMStreamResponse(
          content="",
          provider=self.provider_name,
          model=self.config.model,
          is_complete=True,
          error=str(e)
      )

  def _convert_messages(self, messages: List[Message]) -> List[MessageParam]:
    """Convert internal message format to Anthropic format"""
    anthropic_messages = []

    for msg in messages:
      # Map roles
      if msg.role == "assistant":
        role = "assistant"
      elif msg.role == "user":
        role = "user"
      elif msg.role == "system":
        # System messages are handled separately in Anthropic
        continue
      else:
        role = "user"  # Default fallback

      anthropic_messages.append({
          "role": role,
          "content": msg.content
      })

    return anthropic_messages

  def _estimate_tokens(self, text: str) -> int:
    """Estimate token count for Anthropic (rough approximation)"""
    # Anthropic uses a different tokenizer, this is a rough estimate
    # In production, you might want to use the actual tokenizer
    return max(1, len(text.split()) * 1.3)

  async def get_available_models(self) -> List[str]:
    """Get list of available Anthropic models"""
    return [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2"
    ]

  async def validate_configuration(self) -> bool:
    """Validate Anthropic provider configuration"""
    try:
      # Test with a minimal request
      response = await self.client.messages.create(
          model=self.config.model,
          messages=[{"role": "user", "content": "test"}],
          max_tokens=1
      )
      logger.info("Anthropic configuration validation successful")
      return True
    except Exception as e:
      logger.error(f"Anthropic configuration validation failed: {str(e)}")
      return False
