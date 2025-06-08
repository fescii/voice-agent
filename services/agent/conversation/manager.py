"""
Simplified conversation manager using modular structure.
"""

from typing import Dict, Any, Optional
from .processing.processor import ConversationProcessor
from .flow.definitions import ConversationFlow

# Re-export for backward compatibility
from .flow.definitions import ConversationFlow, ConversationTurn


class ConversationManager:
  """Simplified conversation manager that delegates to modular components."""

  def __init__(self, agent_core):
    """Initialize conversation manager."""
    self.processor = ConversationProcessor(agent_core)

  async def process_conversation_turn(
      self,
      user_input: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ):
    """Process a conversation turn with flow management."""
    return await self.processor.process_turn(user_input, audio_data, metadata)

  def get_conversation_flow(self) -> ConversationFlow:
    """Get current conversation flow."""
    return self.processor.get_conversation_flow()

  def set_conversation_flow(self, flow: ConversationFlow):
    """Set conversation flow."""
    self.processor.set_conversation_flow(flow)

  async def get_conversation_stats(self) -> Dict[str, Any]:
    """Get conversation statistics."""
    return await self.processor.get_conversation_stats()
