"""
Call operations manager for handling call control operations.
"""
from typing import Dict, Optional, Any, Optional, Any
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

  async def get_call_status(self, call_id: str) -> Optional[Dict[str, Any]]:
    """
    Get status information for a specific call.

    Args:
        call_id: Call identifier

    Returns:
        Dictionary with call status information
    """
    try:
      call_context = self.active_calls.get(call_id)
      if not call_context:
        return None

      return {
          "call_id": call_context.call_id,
          "status": call_context.status.value,
          "phone_number": call_context.phone_number,
          "agent_id": call_context.agent_id,
          "direction": call_context.direction.value,
          "start_time": call_context.start_time.isoformat() if call_context.start_time else None,
          "duration": call_context.duration,
          "metadata": call_context.metadata
      }

    except Exception as e:
      logger.error(f"Failed to get call status for {call_id}: {e}")
      return None

  async def get_call_metrics(self) -> Dict[str, Any]:
    """
    Get overall call metrics.

    Returns:
        Dictionary with call metrics
    """
    try:
      total_calls = len(self.active_calls)
      answered_calls = sum(1 for call in self.active_calls.values()
                           if call.status.value == "answered")

      return {
          "total_active_calls": total_calls,
          "answered_calls": answered_calls,
          "pending_calls": total_calls - answered_calls,
          "timestamp": datetime.now(timezone.utc).isoformat()
      }

    except Exception as e:
      logger.error(f"Failed to get call metrics: {e}")
      return {}

  async def update_call_context(self, call_id: str, context_updates: Dict[str, Any]) -> bool:
    """
    Update call context with new information.

    Args:
        call_id: Call identifier
        context_updates: Dictionary of updates to apply

    Returns:
        True if update was successful
    """
    try:
      call_context = self.active_calls.get(call_id)
      if not call_context:
        logger.warning(f"No active call found for update: {call_id}")
        return False

      # Update metadata
      if "metadata" in context_updates:
        call_context.metadata.update(context_updates["metadata"])

      # Update other fields if provided
      for field, value in context_updates.items():
        if field != "metadata" and hasattr(call_context, field):
          setattr(call_context, field, value)

      logger.info(f"Updated call context for {call_id}")
      return True

    except Exception as e:
      logger.error(f"Failed to update call context for {call_id}: {e}")
      return False

  async def pause_call(self, call_id: str) -> bool:
    """
    Pause a call (put on hold).

    Args:
        call_id: Call identifier

    Returns:
        True if call was paused successfully
    """
    try:
      call_context = self.active_calls.get(call_id)
      if not call_context:
        logger.warning(f"No active call found to pause: {call_id}")
        return False

      # TODO: Implement actual pause logic with Ringover API
      call_context.metadata["paused"] = True
      call_context.metadata["paused_at"] = datetime.now(
          timezone.utc).isoformat()

      logger.info(f"Call {call_id} paused")
      return True

    except Exception as e:
      logger.error(f"Failed to pause call {call_id}: {e}")
      return False

  async def resume_call(self, call_id: str) -> bool:
    """
    Resume a paused call.

    Args:
        call_id: Call identifier

    Returns:
        True if call was resumed successfully
    """
    try:
      call_context = self.active_calls.get(call_id)
      if not call_context:
        logger.warning(f"No active call found to resume: {call_id}")
        return False

      # TODO: Implement actual resume logic with Ringover API
      call_context.metadata["paused"] = False
      call_context.metadata["resumed_at"] = datetime.now(
          timezone.utc).isoformat()

      logger.info(f"Call {call_id} resumed")
      return True

    except Exception as e:
      logger.error(f"Failed to resume call {call_id}: {e}")
      return False
