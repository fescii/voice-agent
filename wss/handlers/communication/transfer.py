"""
WebSocket call transfer handlers.
"""

from datetime import datetime
from typing import Dict, Any

from wss.connection import WebSocketConnection
from services.call.management.supervisor import CallSupervisor
from core.logging.setup import get_logger

logger = get_logger(__name__)


class TransferHandler:
  """Handles call transfer operations."""

  def __init__(self, call_supervisor: CallSupervisor):
    """Initialize transfer handler."""
    self.call_supervisor = call_supervisor

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

      if not isinstance(target_number, str):
        await connection.send_message("error", {
            "message": "Target number must be a string",
            "code": "INVALID_TARGET_TYPE"
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
