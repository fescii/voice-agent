"""
WebSocket DTMF tone handlers.
"""

from datetime import datetime
from typing import Dict, Any

from wss.connection import WebSocketConnection
from services.call.management.supervisor import CallSupervisor
from core.logging.setup import get_logger

logger = get_logger(__name__)


class DTMFHandler:
  """Handles DTMF tone operations."""

  def __init__(self, call_supervisor: CallSupervisor):
    """Initialize DTMF handler."""
    self.call_supervisor = call_supervisor

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
      if not tone or not isinstance(tone, str) or tone not in "0123456789*#ABCD":
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
