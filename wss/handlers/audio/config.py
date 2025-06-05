"""
WebSocket audio configuration handlers.
"""

from typing import Dict, Any

from wss.connection import WebSocketConnection
from core.logging.setup import get_logger

logger = get_logger(__name__)


class AudioConfigHandler:
  """Handles audio configuration for WebSocket connections."""

  async def handle_audio_config(self, connection: WebSocketConnection, data: Dict[str, Any]) -> None:
    """Handle audio configuration message"""
    try:
      format_name = data.get("format", "pcm_16000")
      sample_rate = data.get("sample_rate", 16000)
      channels = data.get("channels", 1)

      # Validate and set audio format
      if format_name in ["pcm_16000", "mulaw_8000", "opus"]:
        # Set audio format on connection if supported
        if hasattr(connection, 'audio_format') and hasattr(connection.audio_format, '__class__'):
          connection.audio_format = getattr(
              connection.audio_format.__class__, format_name.upper(), connection.audio_format)

        # Update metadata if available
        metadata = getattr(connection, 'metadata', {})
        metadata.update({
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
