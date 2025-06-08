"""
WebSocket text message handlers.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from wss.connection import WebSocketConnection
from services.agent.core import AgentService
from services.tts.elevenlabs import ElevenLabsService
from core.logging.setup import get_logger

logger = get_logger(__name__)


class TextMessageHandler:
  """Handles text message processing."""

  def __init__(self, tts_service: ElevenLabsService):
    """Initialize text message handler."""
    self.tts_service = tts_service

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

      # Try different method names for text processing
      response = None
      for method_name in ['process_text', 'process_text_input', 'handle_text', 'process_message']:
        if hasattr(agent_service, method_name):
          method = getattr(agent_service, method_name)
          try:
            response = await method(
                call_context=connection.call_context,
                text=text
            )
            break
          except Exception:
            continue

      if not response:
        # Fallback response if no processing method is available
        response = type('Response', (), {
            'text': f"Received: {text}",
            'should_speak': True
        })()

      if response:
        # Send text response back
        response_text = getattr(response, 'text', str(response))
        await connection.send_message("agent_response", {
            "text": response_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Generate and send audio response
        should_speak = getattr(response, 'should_speak', True)
        if should_speak:
          audio_data = await self.tts_service.synthesize_speech(response_text)
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
