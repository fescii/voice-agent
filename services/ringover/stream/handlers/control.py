"""
Control handlers for audio control operations.
"""
from typing import Dict, Any

from core.logging.setup import get_logger

logger = get_logger(__name__)


class ControlHandler:
  """Handler for audio control operations."""

  def __init__(self, connection_manager):
    """
    Initialize control handler.

    Args:
        connection_manager: Connection manager instance
    """
    self.connection_manager = connection_manager
    self._muted = False

  @property
  def is_muted(self) -> bool:
    """Check if audio is muted."""
    return self._muted

  async def mute(self, call_id: str) -> bool:
    """
    Mute audio for the call.

    Args:
        call_id: ID of the call to mute

    Returns:
        True if successful, False otherwise  
    """
    success = await self.connection_manager.send_control_message(call_id, "mute")
    if success:
      self._muted = True
    return success

  async def unmute(self, call_id: str) -> bool:
    """
    Unmute audio for the call.

    Args:
        call_id: ID of the call to unmute

    Returns:
        True if successful, False otherwise
    """
    success = await self.connection_manager.send_control_message(call_id, "unmute")
    if success:
      self._muted = False
    return success

  async def set_volume(self, call_id: str, volume: float) -> bool:
    """
    Set audio volume for the call.

    Args:
        call_id: ID of the call
        volume: Volume level (0.0 to 1.0)

    Returns:
        True if successful, False otherwise
    """
    return await self.connection_manager.send_control_message(
        call_id, "set_volume", {"volume": volume}
    )
