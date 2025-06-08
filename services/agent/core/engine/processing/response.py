"""
Response processing and LLM response handling.
"""
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from models.external.llm.response import LLMResponse
from ...response import AgentResponse

logger = get_logger(__name__)


class ResponseProcessor:
  """Processes LLM responses and formats them for output."""

  def __init__(self, agent_core):
    """Initialize the response processor."""
    self.agent_core = agent_core

  async def process_llm_response(self, llm_response: LLMResponse) -> AgentResponse:
    """Process LLM response and extract actions."""
    try:
      response_text = llm_response.get_content().strip()
      confidence = 1.0  # Default confidence for successful LLM response

      # Extract any special actions or commands from response
      action = None
      if response_text.startswith("/"):
        # Command format: /action_name response_text
        parts = response_text.split(" ", 1)
        if len(parts) > 1:
          action = parts[0][1:]  # Remove leading /
          response_text = parts[1]

      # Clean up response text for speech
      response_text = self._clean_response_for_speech(response_text)

      return AgentResponse(
          text=response_text,
          action=action,
          confidence=confidence,
          metadata={"llm_id": llm_response.id, "model": llm_response.model}
      )

    except Exception as e:
      logger.error(f"Error processing LLM response: {str(e)}")
      return AgentResponse(
          text="I apologize, I didn't understand that completely. Could you please rephrase?",
          confidence=0.5
      )

  def _clean_response_for_speech(self, text: str) -> str:
    """Clean response text for natural speech synthesis."""
    # Remove markdown formatting
    text = text.replace("*", "").replace("_", "").replace("`", "")

    # Remove excessive punctuation
    text = text.replace("...", " pause ")

    # Ensure proper sentence ending
    if text and not text.endswith((".", "!", "?")):
      text += "."

    return text.strip()
