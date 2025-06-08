"""
WebSocket connection enums and constants.
"""

from enum import Enum


class ConnectionState(Enum):
  """WebSocket connection states"""
  CONNECTING = "connecting"
  CONNECTED = "connected"
  AUTHENTICATED = "authenticated"
  IN_CALL = "in_call"
  DISCONNECTED = "disconnected"
  ERROR = "error"


class AudioFormat(Enum):
  """Supported audio formats"""
  PCM_16000 = "pcm_16000"
  MULAW_8000 = "mulaw_8000"
  OPUS = "opus"
