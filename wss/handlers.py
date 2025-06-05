"""
WebSocket Event Handlers
Handles different types of WebSocket messages and events.
"""

import asyncio
import json
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .connection import WebSocketConnection, ConnectionState
from services.audio.streaming import AudioStreamService
from services.agent.core import AgentService
from services.call.management.supervisor import CallSupervisor
from services.stt.whisper_service import WhisperSTTService
from services.tts.elevenlabs_service import ElevenLabsTTSService
from core.logging import get_logger

logger = get_logger(__name__)


class WebSocketHandlers:
  """Handles WebSocket events and message routing"""

  def __init__(self):
    self.audio_stream_service = AudioStreamService()
    self.call_supervisor = CallSupervisor()
    self.stt_service = WhisperSTTService()
    self.tts_service = ElevenLabsTTSService()

    # Message handlers mapping
    self.message_handlers: Dict[str, Callable] = {
        "authenticate": self.handle_authentication,
        "start_call": self.handle_start_call,
        "end_call": self.handle_end_call,
        "audio_config": self.handle_audio_config,
        "text_message": self.handle_text_message,
        "ping": self.handle_ping,
        "mute": self.handle_mute,
        "unmute": self.handle_unmute,
        "transfer": self.handle_transfer,
        "dtmf": self.handle_dtmf
    }

    logger.info("WebSocket handlers initialized")

  async def handle_connection(self, connection: WebSocketConnection) -> None:
    """Handle a new WebSocket connection"""
    try:
      logger.info(
          f"Handling new WebSocket connection: {connection.connection_id}")

      # Set up message handlers
      for message_type, handler in self.message_handlers.items():
        connection.add_message_handler(message_type, handler)

      # Set up audio handler
      connection.add_audio_handler(self.handle_audio_data)

      # Set up disconnect handler
      connection.add_disconnect_handler(self.handle_disconnect)

      # Send welcome message
      await connection.send_message("welcome", {
          "connection_id": connection.connection_id,
          "server_time": datetime.utcnow().isoformat(),
          "supported_audio_formats": ["pcm_16000", "mulaw_8000", "opus"],
          "protocol_version": "1.0"
      })

      # Start message loop
      await self._message_loop(connection)

    except Exception as e:
      logger.error(
          f"Error handling connection {connection.connection_id}: {str(e)}")
      await connection.close(code=1011, reason="Internal server error")

  async def _message_loop(self, connection: WebSocketConnection) -> None:
    """Main message processing loop for a connection"""
    try:
      while connection.is_active():
        message = await connection.receive_message()
        if message is None:
          break

        await self._process_message(connection, message)

    except Exception as e:
      logger.error(
          f"Message loop error for {connection.connection_id}: {str(e)}")
    finally:
      logger.info(f"Message loop ended for {connection.connection_id}")

  async def _process_message(self, connection: WebSocketConnection, message: Dict[str, Any]) -> None:
    """Process a single message"""
    try:
      message_type = message.get("type")
      if not message_type:
        await connection.send_message("error", {
            "message": "Message type is required",
            "code": "INVALID_MESSAGE"
        })
        return

      handler = connection.message_handlers.get(message_type)
      if not handler:
        await connection.send_message("error", {
            "message": f"Unknown message type: {message_type}",
            "code": "UNKNOWN_MESSAGE_TYPE"
        })
        return

      # Call the handler
      await handler(connection, message.get("data", {}))

    except Exception as e:
      logger.error(
          f"Error processing message {message.get('type')} for {connection.connection_id}: {str(e)}")
      await connection.send_message("error", {
          "message": "Failed to process message",
          "code": "PROCESSING_ERROR"
      })

  async def handle_authentication(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle authentication message"""
    try:
      token = data.get("token")
      if not token:
        await connection.send_message("auth_error", {
            "message": "Token is required",
            "code": "MISSING_TOKEN"
        })
        return

      # Authenticate the connection
      if await connection.authenticate(token):
        await connection.send_message("auth_success", {
            "user_id": connection.user_id,
            "authenticated_at": datetime.utcnow().isoformat()
        })
        logger.info(
            f"Successfully authenticated connection {connection.connection_id}")
      else:
        await connection.send_message("auth_error", {
            "message": "Invalid token",
            "code": "INVALID_TOKEN"
        })

    except Exception as e:
      logger.error(
          f"Authentication error for {connection.connection_id}: {str(e)}")
      await connection.send_message("auth_error", {
          "message": "Authentication failed",
          "code": "AUTH_FAILED"
      })

  async def handle_start_call(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle start call message"""
    try:
      if connection.state != ConnectionState.AUTHENTICATED:
        await connection.send_message("error", {
            "message": "Must be authenticated to start call",
            "code": "NOT_AUTHENTICATED"
        })
        return

      call_id = data.get("call_id")
      agent_id = data.get("agent_id")
      phone_number = data.get("phone_number")

      if not all([call_id, agent_id, phone_number]):
        await connection.send_message("error", {
            "message": "call_id, agent_id, and phone_number are required",
            "code": "MISSING_PARAMETERS"
        })
        return

      # Create call context and start call
      call_context = await self.call_supervisor.start_call(
          call_id=call_id,
          agent_id=agent_id,
          phone_number=phone_number,
          websocket_id=connection.connection_id
      )

      if call_context:
        await connection.start_call(call_context)
        logger.info(
            f"Started call {call_id} for connection {connection.connection_id}")
      else:
        await connection.send_message("error", {
            "message": "Failed to start call",
            "code": "CALL_START_FAILED"
        })

    except Exception as e:
      logger.error(
          f"Error starting call for {connection.connection_id}: {str(e)}")
      await connection.send_message("error", {
          "message": "Failed to start call",
          "code": "CALL_START_ERROR"
      })

  async def handle_end_call(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle end call message"""
    try:
      if not connection.call_context:
        await connection.send_message("error", {
            "message": "No active call to end",
            "code": "NO_ACTIVE_CALL"
        })
        return

      call_id = connection.call_context.call_id
      await self.call_supervisor.end_call(call_id)
      await connection.end_call()

      logger.info(
          f"Ended call {call_id} for connection {connection.connection_id}")

    except Exception as e:
      logger.error(
          f"Error ending call for {connection.connection_id}: {str(e)}")
      await connection.send_message("error", {
          "message": "Failed to end call",
          "code": "CALL_END_ERROR"
      })

  async def handle_audio_config(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle audio configuration message"""
    try:
      format_name = data.get("format", "pcm_16000")
      sample_rate = data.get("sample_rate", 16000)
      channels = data.get("channels", 1)

      # Validate and set audio format
      if format_name in ["pcm_16000", "mulaw_8000", "opus"]:
        connection.audio_format = getattr(
            connection.audio_format.__class__, format_name.upper())
        connection.metadata.update({
            "sample_rate": sample_rate,
            "channels": channels
        })

        await connection.send_message("audio_config_set", {
            "format": format_name,
            "sample_rate": sample_rate,
            "channels": channels
        })

        logger.info(
            f"Set audio config for {connection.connection_id}: {format_name}")
      else:
        await connection.send_message("error", {
            "message": f"Unsupported audio format: {format_name}",
            "code": "UNSUPPORTED_FORMAT"
        })

    except Exception as e:
      logger.error(
          f"Error setting audio config for {connection.connection_id}: {str(e)}")
      await connection.send_message("error", {
          "message": "Failed to set audio configuration",
          "code": "AUDIO_CONFIG_ERROR"
      })

  async def handle_text_message(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle text message from user"""
    try:
      if not connection.call_context:
        await connection.send_message("error", {
            "message": "No active call for text message",
            "code": "NO_ACTIVE_CALL"
        })
        return

      text = data.get("text", "").strip()
      if not text:
        await connection.send_message("error", {
            "message": "Text content is required",
            "code": "EMPTY_TEXT"
        })
        return

      # Process text with agent
      agent_service = AgentService()
      response = await agent_service.process_text_input(
          call_context=connection.call_context,
          text=text
      )

      if response:
        # Send text response back
        await connection.send_message("agent_response", {
            "text": response.text,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Generate and send audio response
        if response.should_speak:
          audio_data = await self.tts_service.synthesize_speech(response.text)
          if audio_data:
            await connection.send_audio(audio_data)

      logger.debug(f"Processed text message for {connection.connection_id}")

    except Exception as e:
      logger.error(
          f"Error processing text message for {connection.connection_id}: {str(e)}")
      await connection.send_message("error", {
          "message": "Failed to process text message",
          "code": "TEXT_PROCESSING_ERROR"
      })

  async def handle_ping(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle ping message"""
    await connection.send_message("pong", {
        "timestamp": datetime.utcnow().isoformat(),
        "connection_id": connection.connection_id
    })

  async def handle_mute(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle mute message"""
    try:
      if connection.call_context:
        connection.metadata["muted"] = True
        await connection.send_message("muted", {
            "call_id": connection.call_context.call_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.info(f"Muted call for connection {connection.connection_id}")
    except Exception as e:
      logger.error(
          f"Error muting call for {connection.connection_id}: {str(e)}")

  async def handle_unmute(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle unmute message"""
    try:
      if connection.call_context:
        connection.metadata["muted"] = False
        await connection.send_message("unmuted", {
            "call_id": connection.call_context.call_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.info(f"Unmuted call for connection {connection.connection_id}")
    except Exception as e:
      logger.error(
          f"Error unmuting call for {connection.connection_id}: {str(e)}")

  async def handle_transfer(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle call transfer message"""
    try:
      if not connection.call_context:
        await connection.send_message("error", {
            "message": "No active call to transfer",
            "code": "NO_ACTIVE_CALL"
        })
        return

      target_number = data.get("target_number")
      if not target_number:
        await connection.send_message("error", {
            "message": "Target number is required for transfer",
            "code": "MISSING_TARGET"
        })
        return

      # Initiate transfer
      success = await self.call_supervisor.transfer_call(
          connection.call_context.call_id,
          target_number
      )

      if success:
        await connection.send_message("call_transferred", {
            "call_id": connection.call_context.call_id,
            "target_number": target_number,
            "timestamp": datetime.utcnow().isoformat()
        })
        logger.info(
            f"Transferred call {connection.call_context.call_id} to {target_number}")
      else:
        await connection.send_message("error", {
            "message": "Transfer failed",
            "code": "TRANSFER_FAILED"
        })

    except Exception as e:
      logger.error(
          f"Error transferring call for {connection.connection_id}: {str(e)}")
      await connection.send_message("error", {
          "message": "Transfer failed",
          "code": "TRANSFER_ERROR"
      })

  async def handle_dtmf(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle DTMF tone message"""
    try:
      if not connection.call_context:
        await connection.send_message("error", {
            "message": "No active call for DTMF",
            "code": "NO_ACTIVE_CALL"
        })
        return

      tone = data.get("tone")
      if tone not in "0123456789*#ABCD":
        await connection.send_message("error", {
            "message": "Invalid DTMF tone",
            "code": "INVALID_DTMF"
        })
        return

      # Send DTMF tone
      success = await self.call_supervisor.send_dtmf(
          connection.call_context.call_id,
          tone
      )

      if success:
        await connection.send_message("dtmf_sent", {
            "call_id": connection.call_context.call_id,
            "tone": tone,
            "timestamp": datetime.utcnow().isoformat()
        })
      else:
        await connection.send_message("error", {
            "message": "DTMF send failed",
            "code": "DTMF_FAILED"
        })

    except Exception as e:
      logger.error(
          f"Error sending DTMF for {connection.connection_id}: {str(e)}")

  async def handle_audio_data(self, audio_data: bytes) -> None:
    """Handle incoming audio data"""
    try:
      # Process audio through STT service
      text = await self.stt_service.transcribe_audio(audio_data)
      if text and text.strip():
        logger.debug(f"Transcribed audio: {text[:50]}...")
        # Further processing would happen here

    except Exception as e:
      logger.error(f"Error processing audio data: {str(e)}")

  async def handle_disconnect(self, connection: WebSocketConnection) -> None:
    """Handle connection disconnect"""
    try:
      logger.info(f"Handling disconnect for {connection.connection_id}")

      # End any active call
      if connection.call_context:
        await self.call_supervisor.end_call(connection.call_context.call_id)

      # Clean up resources
      await self._cleanup_connection_resources(connection)

    except Exception as e:
      logger.error(
          f"Error handling disconnect for {connection.connection_id}: {str(e)}")

  async def _cleanup_connection_resources(self, connection: WebSocketConnection) -> None:
    """Clean up resources associated with a connection"""
    try:
      # Stop any audio streaming
      if hasattr(connection, 'audio_stream'):
        await connection.audio_stream.stop()

      # Clear any cached data
      connection.metadata.clear()

      logger.debug(f"Cleaned up resources for {connection.connection_id}")

    except Exception as e:
      logger.error(
          f"Error cleaning up resources for {connection.connection_id}: {str(e)}")


# Global handlers instance
websocket_handlers = WebSocketHandlers()
