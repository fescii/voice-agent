"""
Call operations manager for handling call control operations.
"""
from typing import Dict
from datetime import datetime, timezone

from models.internal.callcontext import CallContext
from core.logging.setup import get_logger

logger = get_logger(__name__)


class CallOperationsManager:
  """Manages call operations like transfer and DTMF."""

  def __init__(self, active_calls: Dict[str, CallContext]):
    """Initialize with reference to active calls."""
    self.active_calls = active_calls

  async def transfer_call(self, call_id: str, target_number: str) -> bool:
    """
    Transfer a call to another number.

    Args:
        call_id: Call identifier to transfer
        target_number: Target phone number

    Returns:
        True if transfer was initiated successfully
    """
    try:
      call_context = self.active_calls.get(call_id)
      if not call_context:
        logger.warning(f"No active call found for transfer: {call_id}")
        return False

      # TODO: Implement actual transfer logic with Ringover API
      # For now, just log and return success
      logger.info(
          f"Transfer initiated for call {call_id} to {target_number}")

      # Update call context
      call_context.metadata["transfer_target"] = target_number
      call_context.metadata["transfer_initiated_at"] = datetime.now(
          timezone.utc).isoformat()

      return True

    except Exception as e:
      logger.error(f"Failed to transfer call {call_id}: {e}")
      return False

  async def send_dtmf(self, call_id: str, tone: str) -> bool:
    """
    Send DTMF tone to a call.

    Args:
        call_id: Call identifier
        tone: DTMF tone to send

    Returns:
        True if DTMF was sent successfully
    """
    try:
      call_context = self.active_calls.get(call_id)
      if not call_context:
        logger.warning(f"No active call found for DTMF: {call_id}")
        return False

      # TODO: Implement actual DTMF sending with Ringover API
      # For now, just log and return success
      logger.info(f"DTMF tone '{tone}' sent to call {call_id}")

      # Track DTMF in metadata
      if "dtmf_tones" not in call_context.metadata:
        call_context.metadata["dtmf_tones"] = []
      call_context.metadata["dtmf_tones"].append({
          "tone": tone,
          "timestamp": datetime.now(timezone.utc).isoformat()
      })

      return True

    except Exception as e:
      logger.error(f"Failed to send DTMF to call {call_id}: {e}")
      return False
