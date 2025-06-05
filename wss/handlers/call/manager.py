"""
WebSocket call management handlers.
"""

from typing import Dict, Any

from wss.connection import WebSocketConnection, ConnectionState
from services.call.management.supervisor import CallSupervisor
from core.logging.setup import get_logger

logger = get_logger(__name__)


class CallHandler:
  """Handles call management WebSocket messages."""

  def __init__(self, call_supervisor: CallSupervisor):
    """Initialize call handler."""
    self.call_supervisor = call_supervisor

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

      # Type checking to ensure values are strings
      if not isinstance(call_id, str) or not isinstance(agent_id, str) or not isinstance(phone_number, str):
        await connection.send_message("error", {
            "message": "call_id, agent_id, and phone_number must be strings",
            "code": "INVALID_PARAMETER_TYPE"
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
