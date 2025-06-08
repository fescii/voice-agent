"""
WebSocket handlers initialization.
"""

from ..auth import AuthHandler
from ..call import CallHandler
from ..audio import AudioConfigHandler, AudioDataHandler, AudioControlHandler
from ..communication import TextMessageHandler, PingHandler, TransferHandler, DTMFHandler
from ..connection import DisconnectHandler
from core.logging.setup import get_logger

logger = get_logger(__name__)


class HandlerInitializer:
  """Initializes all WebSocket message handlers."""

  def __init__(self, services):
    self.services = services
    self.handlers = {}

  def initialize(self):
    """Initialize all handlers."""
    # Initialize handlers with required services
    self.handlers = {
        'auth': AuthHandler(),
        'call': CallHandler(self.services['call_supervisor']),
        'audio_config': AudioConfigHandler(),
        'audio_data': None,  # TODO: AudioDataHandler(self.services['stt'])
        'audio_control': AudioControlHandler(),
        'text': None,  # TODO: TextMessageHandler(self.services['tts'])
        'ping': PingHandler(),
        'transfer': TransferHandler(self.services['call_supervisor']),
        'dtmf': DTMFHandler(self.services['call_supervisor']),
        'disconnect': DisconnectHandler(self.services['call_supervisor'])
    }

    logger.info("WebSocket handlers initialized")

  def get_handlers(self):
    """Get initialized handlers."""
    return self.handlers
