"""
Gemini LLM provider implementation.
"""
import os
import asyncio
from typing import List, Dict, Any, AsyncIterator, Optional
from datetime import datetime

try:
  import google.generativeai as genai
  from google.generativeai.types import HarmCategory, HarmBlockThreshold, GenerationConfig
  GEMINI_AVAILABLE = True
except ImportError:
  GEMINI_AVAILABLE = False
  genai = None
  HarmCategory = None
  HarmBlockThreshold = None
  GenerationConfig = None

from .base import BaseLLMProvider
from models.external.llm.request import LLMRequest, LLMMessage
from models.external.llm.response import LLMResponse, LLMChoice, LLMUsage
from models.external.llm.response import LLMMessage as ResponseLLMMessage
from core.config.services.llm.gemini import GeminiConfig
from core.logging import get_logger

logger = get_logger(__name__)


class GeminiProvider(BaseLLMProvider):
  """Google Gemini LLM provider."""

  def __init__(self, config: Optional[Dict[str, Any]] = None):
    if config is None:
      config = GeminiConfig().dict()
    super().__init__(config)

    self.logger = logger
    self.provider_name = "gemini"

    if not GEMINI_AVAILABLE:
      self.logger.error(
          "google-generativeai package not installed. Install with: pip install google-generativeai")
      self.client = None
      return

    # Configure Gemini
    api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY")
    if not api_key:
      self.logger.error(
          "Gemini API key not found in config or GEMINI_API_KEY environment variable")
      self.client = None
      return

    genai.configure(api_key=api_key)  # type: ignore

    # Initialize model
    model_name = config.get("model", "gemini-1.5-flash")

    # Safety settings for voice agents - more permissive for business use
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # type: ignore
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # type: ignore
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # type: ignore
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,  # type: ignore
    }

    try:
      self.client = genai.GenerativeModel(  # type: ignore
          model_name=model_name,
          safety_settings=safety_settings
      )
      self.logger.info(f"Initialized Gemini provider with model: {model_name}")
    except Exception as e:
      self.logger.error(f"Failed to initialize Gemini client: {e}")
      self.client = None

  def _convert_messages_to_gemini_format(self, messages: List[LLMMessage]) -> str:
    """Convert messages to a single prompt string for Gemini."""
    prompt_parts = []

    for message in messages:
      if message.role == "system":
        prompt_parts.append(f"[System]: {message.content}")
      elif message.role == "user":
        prompt_parts.append(f"Human: {message.content}")
      elif message.role == "assistant":
        prompt_parts.append(f"Assistant: {message.content}")

    # Add instruction for the assistant to respond
    if not any(msg.role == "assistant" for msg in messages[-1:]):
      prompt_parts.append("Assistant:")

    return "\n\n".join(prompt_parts)

  async def generate_response(self, request: LLMRequest) -> LLMResponse:
    """Generate response using Gemini API."""
    if not self.client:
      raise RuntimeError("Gemini client not initialized")

    try:
      # Convert messages to prompt string
      prompt = self._convert_messages_to_gemini_format(request.messages)

      # Generation config
      generation_config = GenerationConfig(  # type: ignore
          temperature=request.temperature,
          max_output_tokens=request.max_tokens,
          stop_sequences=request.stop_sequences
      )

      # Generate response
      response = await asyncio.to_thread(
          self.client.generate_content,
          prompt,
          generation_config=generation_config
      )

      # Parse response
      content = response.text if response.text else ""

      # Create response object
      choice = LLMChoice(
          message=ResponseLLMMessage(role="assistant", content=content),
          finish_reason=getattr(
              response.candidates[0], 'finish_reason', None) if response.candidates else None,
          index=0
      )

      # Calculate approximate usage (Gemini doesn't provide detailed token counts in all cases)
      usage = None
      if hasattr(response, 'usage_metadata') and response.usage_metadata:
        usage = LLMUsage(
            prompt_tokens=getattr(response.usage_metadata,
                                  'prompt_token_count', 0),
            completion_tokens=getattr(
                response.usage_metadata, 'candidates_token_count', 0),
            total_tokens=getattr(response.usage_metadata,
                                 'total_token_count', 0)
        )

      return LLMResponse(
          id=f"gemini-{datetime.utcnow().isoformat()}",
          provider=self.provider_name,
          model=request.model,
          choices=[choice],
          usage=usage,
          raw_response={"response": str(response)}
      )

    except Exception as e:
      self.logger.error(f"Gemini API error: {e}")
      raise RuntimeError(f"Gemini generation failed: {e}")

  async def stream_response(self, request: LLMRequest) -> AsyncIterator[str]:
    """Stream response from Gemini API."""
    if not self.client:
      raise RuntimeError("Gemini client not initialized")

    try:
      # Convert messages to prompt string
      prompt = self._convert_messages_to_gemini_format(request.messages)

      # Generation config for streaming
      generation_config = GenerationConfig(  # type: ignore
          temperature=request.temperature,
          max_output_tokens=request.max_tokens,
          stop_sequences=request.stop_sequences
      )

      # Generate streaming response
      response_stream = await asyncio.to_thread(
          self.client.generate_content,
          prompt,
          generation_config=generation_config,
          stream=True
      )

      # Stream the response chunks
      for chunk in response_stream:
        if chunk.text:
          yield chunk.text

    except Exception as e:
      self.logger.error(f"Gemini streaming error: {e}")
      raise RuntimeError(f"Gemini streaming failed: {e}")

  async def validate_config(self) -> bool:
    """Validate Gemini configuration."""
    if not GEMINI_AVAILABLE:
      self.logger.error("google-generativeai package not available")
      return False

    if not self.client:
      self.logger.error("Gemini client not initialized")
      return False

    try:
      # Test with a simple generation
      test_response = await asyncio.to_thread(
          self.client.generate_content,
          "Hello"
      )

      if test_response and test_response.text:
        self.logger.info("Gemini configuration validated successfully")
        return True
      else:
        self.logger.error("Gemini test generation returned empty response")
        return False

    except Exception as e:
      self.logger.error(f"Gemini configuration validation failed: {e}")
      return False

  def get_available_models(self) -> List[str]:
    """Get list of available Gemini models."""
    return [
        # Gemini Pro Models (Latest)
        "gemini-1.5-pro",
        "gemini-1.5-pro-002",
        "gemini-1.5-pro-001",
        "gemini-1.5-flash",
        "gemini-1.5-flash-002",
        "gemini-1.5-flash-001",
        "gemini-1.5-flash-8b",

        # Gemini 1.0 Pro Models
        "gemini-1.0-pro",
        "gemini-1.0-pro-001",
        "gemini-pro",  # Alias for backward compatibility

        # Experimental/Vision Models
        "gemini-1.5-pro-vision-latest",
        "gemini-pro-vision"
    ]
