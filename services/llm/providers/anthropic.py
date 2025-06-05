"""
Anthropic LLM Provider Implementation
Handles Claude model interactions for the Voice Agent system.
"""

from typing import List, Dict, Any, Optional, AsyncIterator
import anthropic
from anthropic.types import MessageParam

from .base import BaseLLMProvider
from models.external.llm.request import LLMRequest
from models.external.llm.request import LLMMessage as RequestLLMMessage
from models.external.llm.response import LLMResponse, LLMChoice, LLMUsage
from models.external.llm.response import LLMMessage as ResponseLLMMessage
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AnthropicProvider(BaseLLMProvider):
  """Anthropic Claude LLM Provider"""

  def __init__(self, config: Dict[str, Any]):
    super().__init__(config)
    self.logger = logger
    self.provider_name = "anthropic"

    # Initialize Anthropic client
    api_key = config.get("api_key")
    if not api_key:
      raise ValueError("Anthropic API key is required")

    self.client = anthropic.AsyncAnthropic(
        api_key=api_key,
        timeout=config.get("timeout", 30.0)
    )

    self.model = config.get("model", "claude-3-5-sonnet-20241022")
    self.temperature = config.get("temperature", 0.7)
    self.max_tokens = config.get("max_tokens", 1024)

    logger.info(f"Initialized Anthropic provider with model: {self.model}")

  async def generate_response(self, request: LLMRequest) -> LLMResponse:
    """Generate a response using Anthropic Claude"""
    try:
      # Convert messages to Anthropic format
      messages = self._convert_messages(request.messages)

      # Prepare request parameters
      params = {
          "model": request.model or self.model,
          "messages": messages,
          "max_tokens": request.max_tokens or self.max_tokens,
          "temperature": request.temperature if request.temperature is not None else self.temperature,
      }

      # Add system prompt if provided in extra_params
      if "system_prompt" in request.extra_params:
        params["system"] = request.extra_params["system_prompt"]

      # Add optional parameters from extra_params
      if "top_p" in request.extra_params:
        params["top_p"] = request.extra_params["top_p"]

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

      # Create choices in the expected format
      choice = LLMChoice(
          message=ResponseLLMMessage(role="assistant", content=content),
          finish_reason=response.stop_reason or "stop",
          index=0
      )

      # Create usage information
      usage = None
      if hasattr(response, 'usage') and response.usage:
        usage = LLMUsage(
            prompt_tokens=getattr(response.usage, 'input_tokens', 0),
            completion_tokens=getattr(response.usage, 'output_tokens', 0),
            total_tokens=getattr(response.usage, 'input_tokens', 0) +
            getattr(response.usage, 'output_tokens', 0)
        )

      return LLMResponse(
          id=getattr(response, 'id', 'anthropic-response'),
          provider=self.provider_name,
          model=response.model,
          choices=[choice],
          usage=usage,
          raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
      )

    except anthropic.APIError as e:
      logger.error(f"Anthropic API error: {str(e)}")
      raise Exception(f"Anthropic API error: {str(e)}")
    except Exception as e:
      logger.error(f"Unexpected error in Anthropic provider: {str(e)}")
      raise Exception(f"Anthropic error: {str(e)}")

  async def stream_response(self, request: LLMRequest) -> AsyncIterator[str]:
    """Stream response from Anthropic Claude"""
    try:
      # Convert messages to Anthropic format
      messages = self._convert_messages(request.messages)

      # Prepare request parameters
      params = {
          "model": request.model or self.model,
          "messages": messages,
          "max_tokens": request.max_tokens or self.max_tokens,
          "temperature": request.temperature if request.temperature is not None else self.temperature,
          "stream": True,
      }

      # Add system prompt if provided in extra_params
      if "system_prompt" in request.extra_params:
        params["system"] = request.extra_params["system_prompt"]

      # Add optional parameters from extra_params
      if "top_p" in request.extra_params:
        params["top_p"] = request.extra_params["top_p"]

      if request.stop_sequences:
        params["stop_sequences"] = request.stop_sequences[:4]

      logger.debug(f"Starting stream from Anthropic: {params['model']}")

      # Use streaming with proper event handling
      stream = await self.client.messages.create(**params)

      async for event in stream:
        # Handle different types of streaming events
        if event.type == "content_block_delta":
          if hasattr(event.delta, 'text'):
            yield event.delta.text
        elif event.type == "content_block_start":
          # Start of content block, might contain initial text
          if hasattr(event.content_block, 'text'):
            yield event.content_block.text

    except anthropic.APIError as e:
      logger.error(f"Anthropic streaming error: {str(e)}")
      raise Exception(f"Anthropic streaming error: {str(e)}")
    except Exception as e:
      logger.error(f"Unexpected streaming error: {str(e)}")
      raise Exception(f"Anthropic streaming error: {str(e)}")

  async def validate_config(self) -> bool:
    """Validate Anthropic provider configuration"""
    try:
      # Test with a minimal request
      response = await self.client.messages.create(
          model=self.model,
          messages=[{"role": "user", "content": "test"}],
          max_tokens=1
      )
      logger.info("Anthropic configuration validation successful")
      return True
    except Exception as e:
      logger.error(f"Anthropic configuration validation failed: {str(e)}")
      return False

  def _convert_messages(self, messages: List[RequestLLMMessage]) -> List[MessageParam]:
    """Convert internal message format to Anthropic format"""
    anthropic_messages = []

    for msg in messages:
      # Map roles - skip system messages as they're handled separately
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

  def get_available_models(self) -> List[str]:
    """Get list of available Anthropic models"""
    return [
        # Claude 3.5 Models (Latest)
        "claude-3-5-sonnet-20241022",
        "claude-3-5-sonnet-20240620",
        "claude-3-5-haiku-20241022",

        # Claude 3 Models
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",

        # Legacy Claude Models
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2"
    ]
