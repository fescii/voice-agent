"""
Conversation context management.
"""

from typing import Dict, Any, Optional
from core.logging.setup import get_logger

logger = get_logger(__name__)


class ConversationContextManager:
  """Manages conversation context and history."""

  def __init__(self):
    """Initialize conversation context manager."""
    self.context = {}

  async def update_context(self, user_input: str, response, extracted_info: Optional[Dict[str, Any]] = None):
    """Update conversation context with new information."""
    try:
      # Store extracted information
      if extracted_info:
        self.context.update(extracted_info)

      # Store response metadata
      if hasattr(response, 'metadata') and response.metadata:
        self.context.update(response.metadata)

    except Exception as e:
      logger.warning(f"Error updating conversation context: {str(e)}")

  def get_context(self) -> Dict[str, Any]:
    """Get current conversation context."""
    return self.context.copy()

  def set_context_item(self, key: str, value: Any):
    """Set a specific context item."""
    self.context[key] = value

  def get_context_item(self, key: str, default: Any = None) -> Any:
    """Get a specific context item."""
    return self.context.get(key, default)

  def clear_context(self):
    """Clear conversation context."""
    self.context.clear()

  def has_key(self, key: str) -> bool:
    """Check if context has a specific key."""
    return key in self.context
