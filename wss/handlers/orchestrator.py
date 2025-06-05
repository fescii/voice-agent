"""
Main WebSocket handlers orchestrator.
"""

from typing import Dict, Any, Callable

from wss.connection import WebSocketConnection
from services.audio.streaming import AudioStreamService
from services.call.management.supervisor import CallSupervisor
from services.stt.whisper import WhisperService
from services.tts.elevenlabs import ElevenLabsService
from core.config.services.stt.whisper import WhisperConfig
from core.config.services.tts.elevenlabs import ElevenLabsConfig
from core.logging.setup import get_logger

from .connection import ConnectionManager, DisconnectHandler
from .auth import AuthHandler
from .call import CallHandler
from .audio import AudioConfigHandler, AudioDataHandler, AudioControlHandler
from .communication import TextMessageHandler, PingHandler, TransferHandler, DTMFHandler

logger = get_logger(__name__)


class WebSocketHandlers:
  """Main WebSocket handlers orchestrator that delegates to specialized handlers."""

  def __init__(self):
    # Initialize services with default configs
    self.audio_stream_service = AudioStreamService()
    self.call_supervisor = CallSupervisor()
    self.stt_service = WhisperService(WhisperConfig())
    self.tts_service = ElevenLabsService(ElevenLabsConfig())

    # Initialize specialized handlers
    self.auth_handler = AuthHandler()
    self.call_handler = CallHandler(self.call_supervisor)
    self.audio_config_handler = AudioConfigHandler()
    self.audio_data_handler = AudioDataHandler(self.stt_service)
    self.audio_control_handler = AudioControlHandler()
    self.text_handler = TextMessageHandler(self.tts_service)
    self.ping_handler = PingHandler()
    self.transfer_handler = TransferHandler(self.call_supervisor)
    self.dtmf_handler = DTMFHandler(self.call_supervisor)
    self.disconnect_handler = DisconnectHandler(self.call_supervisor)

    # Create message handlers mapping
    self.message_handlers: Dict[str, Callable] = {
        "authenticate": self.auth_handler.handle_authentication,
        "start_call": self.call_handler.handle_start_call,
        "end_call": self.call_handler.handle_end_call,
        "audio_config": self.audio_config_handler.handle_audio_config,
        "text_message": self.text_handler.handle_text_message,
        "ping": self.ping_handler.handle_ping,
        "mute": self.audio_control_handler.handle_mute,
        "unmute": self.audio_control_handler.handle_unmute,
        "transfer": self.transfer_handler.handle_transfer,
        "dtmf": self.dtmf_handler.handle_dtmf
    }

    # Initialize connection manager
    self.connection_manager = ConnectionManager(
        message_handlers=self.message_handlers,
        audio_handler=self.audio_data_handler.handle_audio_data,
        disconnect_handler=self.disconnect_handler.handle_disconnect
    )

    logger.info("WebSocket handlers initialized")

  async def handle_connection(self, connection: WebSocketConnection) -> None:
    """Handle a new WebSocket connection by delegating to connection manager."""
    await self.connection_manager.handle_connection(connection)


# Global handlers instance
websocket_handlers = WebSocketHandlers()
