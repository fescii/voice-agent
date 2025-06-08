"""
Information gathering flow handler.
"""

from typing import Dict, Any
from core.logging.setup import get_logger

logger = get_logger(__name__)


class GatheringHandler:
  """Handles information gathering flow processing."""

  def __init__(self, extractor, context_manager):
    """Initialize gathering handler."""
    self.extractor = extractor
    self.context_manager = context_manager

  async def handle(self, user_input: str, base_response, metadata: Dict[str, Any]):
    """Handle information gathering flow."""
    # Extract information from user input
    extracted_info = await self.extractor.extract_information(user_input)

    # Update conversation context with extracted info
    await self.context_manager.update_context(user_input, base_response, extracted_info)

    # Check if we have enough information
    if await self.extractor.has_sufficient_information(self.context_manager.get_context()):
      # Move to processing
      enhanced_text = "Thank you for that information. Let me help you with that."
      next_flow = "processing_request"
    else:
      # Ask for more information
      missing_info = await self.extractor.identify_missing_information(self.context_manager.get_context())
      enhanced_text = f"{base_response.text} Could you also tell me about {missing_info}?"
      next_flow = "gathering_info"

    from services.agent.core import AgentResponse
    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        metadata={**(base_response.metadata or {}), "flow": "gathering_info",
                  "extracted_info": extracted_info, "next_flow": next_flow}
    )
