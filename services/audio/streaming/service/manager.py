"""
Service for managing audio streams in WebSocket connections.
"""

from core.logging.setup import get_logger
from services.audio.processor import AudioProcessor, AudioFormat
from ..config import StreamingConfig
from ..processor import StreamingProcessor

logger = get_logger(__name__)


class AudioStreamService:
  """Service for managing audio streams in WebSocket connections."""

  def __init__(self):
    self.config = StreamingConfig()
    self.active_streams = {}

  async def start_stream(self, connection_id: str, audio_format: AudioFormat):
    """Start an audio stream for a connection."""
    try:
      logger.info(f"Starting audio stream for connection {connection_id}")
      # Initialize stream processor
      processor = StreamingProcessor(self.config, AudioProcessor())
      self.active_streams[connection_id] = {
          'processor': processor,
          'format': audio_format,
          'active': True
      }
      return True
    except Exception as e:
      logger.error(f"Failed to start audio stream: {e}")
      return False

  async def stop_stream(self, connection_id: str):
    """Stop an audio stream for a connection."""
    try:
      if connection_id in self.active_streams:
        stream_info = self.active_streams[connection_id]
        stream_info['active'] = False
        del self.active_streams[connection_id]
        logger.info(f"Stopped audio stream for connection {connection_id}")
      return True
    except Exception as e:
      logger.error(f"Failed to stop audio stream: {e}")
      return False

  async def process_audio_chunk(self, connection_id: str, chunk: bytes):
    """Process an audio chunk for a connection."""
    try:
      if connection_id not in self.active_streams:
        logger.warning(f"No active stream for connection {connection_id}")
        return None

      stream_info = self.active_streams[connection_id]
      processor = stream_info['processor']
      audio_format = stream_info['format']

      # Process the chunk
      processed_chunk = await processor._process_chunk(chunk, audio_format)
      return processed_chunk

    except Exception as e:
      logger.error(f"Failed to process audio chunk: {e}")
      return None

  def is_stream_active(self, connection_id: str) -> bool:
    """Check if a stream is active for a connection."""
    return connection_id in self.active_streams and self.active_streams[connection_id]['active']
