"""
WebSocket handler mapping registry.
"""

from typing import Dict, Callable
from core.logging.setup import get_logger

logger = get_logger(__name__)


class HandlerRegistry:
  """Maps message types to handler functions."""

  def __init__(self, handlers):
    self.handlers = handlers
    self.message_handlers = {}

  def register_mappings(self):
    """Register message type to handler function mappings."""
    self.message_handlers = {
        "authenticate": self.handlers['auth'].handle_authentication,
        "start_call": self.handlers['call'].handle_start_call,
        "end_call": self.handlers['call'].handle_end_call,
        "audio_config": self.handlers['audio_config'].handle_audio_config,
        "ping": self.handlers['ping'].handle_ping,
        "mute": self.handlers['audio_control'].handle_mute,
        "unmute": self.handlers['audio_control'].handle_unmute,
        "transfer": self.handlers['transfer'].handle_transfer,
        "dtmf": self.handlers['dtmf'].handle_dtmf
    }

    # TODO: Add these when services are properly configured
    # "text_message": self.handlers['text'].handle_text_message,

    logger.info("Handler mappings registered")

  def get_message_handlers(self) -> Dict[str, Callable]:
    """Get message handler mappings."""
    return self.message_handlers

  def get_audio_handler(self):
    """Get audio handler function."""
    if self.handlers['audio_data']:
      return self.handlers['audio_data'].handle_audio_data
    else:
      return self._stub_audio_handler

  def get_disconnect_handler(self):
    """Get disconnect handler function."""
    return self.handlers['disconnect'].handle_disconnect

  async def _stub_audio_handler(self, data):
    """Stub audio handler until STT service is properly configured."""
    logger.warning("Audio handler not yet implemented")
    pass
