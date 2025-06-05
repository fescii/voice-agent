"""Call state manager for tracking and managing call states."""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Set, Callable, Awaitable, Union

from pydantic import BaseModel

from core.logging.setup import get_logger


class CallState(str, Enum):
  """Call state enumeration."""

  INITIALIZING = "initializing"
  RINGING = "ringing"
  CONNECTED = "connected"
  ON_HOLD = "on_hold"
  MUTED = "muted"
  TRANSFERRING = "transferring"
  RECORDING = "recording"
  ENDING = "ending"
  ENDED = "ended"
  FAILED = "failed"


class CallStateInfo(BaseModel):
  """Call state information model."""

  call_id: str
  state: CallState
  previous_state: Optional[CallState] = None
  timestamp: datetime
  agent_id: Optional[str] = None
  user_id: Optional[str] = None
  metadata: Dict = {}


class CallStateManager:
  """Manages call states across the system."""

  def __init__(self):
    self.logger = get_logger(__name__)
    self._call_states: Dict[str, CallStateInfo] = {}
    self._state_locks: Dict[str, asyncio.Lock] = {}
    self._state_change_callbacks: Dict[str, Set[Callable]] = {}

  async def initialize_call(
      self,
      call_id: str,
      agent_id: Optional[str] = None,
      user_id: Optional[str] = None,
      metadata: Optional[Dict] = None
  ) -> CallStateInfo:
    """Initialize a new call state."""

    self.logger.info(f"Initializing call state for call_id: {call_id}")

    call_state = CallStateInfo(
        call_id=call_id,
        state=CallState.INITIALIZING,
        timestamp=datetime.utcnow(),
        agent_id=agent_id,
        user_id=user_id,
        metadata=metadata or {}
    )

    self._call_states[call_id] = call_state
    self._state_locks[call_id] = asyncio.Lock()

    await self._notify_state_change(call_state)

    return call_state

  async def update_state(
      self,
      call_id: str,
      new_state: CallState,
      metadata: Optional[Dict] = None
  ) -> CallStateInfo:
    """Update call state."""

    if call_id not in self._call_states:
      raise ValueError(f"Call {call_id} not found")

    async with self._state_locks[call_id]:
      current_state = self._call_states[call_id]

      # Validate state transition
      if not self._is_valid_transition(current_state.state, new_state):
        raise ValueError(
            f"Invalid state transition from {current_state.state} to {new_state}"
        )

      # Update state
      updated_state = CallStateInfo(
          call_id=call_id,
          state=new_state,
          previous_state=current_state.state,
          timestamp=datetime.utcnow(),
          agent_id=current_state.agent_id,
          user_id=current_state.user_id,
          metadata={**current_state.metadata, **(metadata or {})}
      )

      self._call_states[call_id] = updated_state

      self.logger.info(
          f"State updated for call {call_id}: {current_state.state} -> {new_state}"
      )

      await self._notify_state_change(updated_state)

      return updated_state

  async def get_state(self, call_id: str) -> Optional[CallStateInfo]:
    """Get current call state."""
    return self._call_states.get(call_id)

  async def remove_call(self, call_id: str) -> None:
    """Remove call from state tracking."""

    if call_id in self._call_states:
      # Update to ended state first
      if self._call_states[call_id].state != CallState.ENDED:
        await self.update_state(call_id, CallState.ENDED)

      # Clean up
      del self._call_states[call_id]
      if call_id in self._state_locks:
        del self._state_locks[call_id]
      if call_id in self._state_change_callbacks:
        del self._state_change_callbacks[call_id]

      self.logger.info(f"Removed call {call_id} from state tracking")

  async def get_active_calls(self) -> Dict[str, CallStateInfo]:
    """Get all active calls."""
    active_states = {
        CallState.INITIALIZING,
        CallState.RINGING,
        CallState.CONNECTED,
        CallState.ON_HOLD,
        CallState.MUTED,
        CallState.TRANSFERRING,
        CallState.RECORDING
    }

    return {
        call_id: state
        for call_id, state in self._call_states.items()
        if state.state in active_states
    }

  def register_state_callback(self, call_id: str, callback: Callable) -> None:
    """Register callback for state changes."""
    if call_id not in self._state_change_callbacks:
      self._state_change_callbacks[call_id] = set()
    self._state_change_callbacks[call_id].add(callback)

  def unregister_state_callback(self, call_id: str, callback: Callable) -> None:
    """Unregister callback for state changes."""
    if call_id in self._state_change_callbacks:
      self._state_change_callbacks[call_id].discard(callback)

  async def _notify_state_change(self, state_info: CallStateInfo) -> None:
    """Notify registered callbacks of state changes."""

    callbacks = self._state_change_callbacks.get(state_info.call_id, set())

    for callback in callbacks:
      try:
        if asyncio.iscoroutinefunction(callback):
          await callback(state_info)
        else:
          callback(state_info)
      except Exception as e:
        self.logger.error(f"Error in state change callback: {e}")

  def _is_valid_transition(self, current: CallState, new: CallState) -> bool:
    """Validate state transitions."""

    # Define valid transitions
    valid_transitions = {
        CallState.INITIALIZING: {
            CallState.RINGING,
            CallState.CONNECTED,
            CallState.FAILED,
            CallState.ENDED
        },
        CallState.RINGING: {
            CallState.CONNECTED,
            CallState.ENDED,
            CallState.FAILED
        },
        CallState.CONNECTED: {
            CallState.ON_HOLD,
            CallState.MUTED,
            CallState.TRANSFERRING,
            CallState.RECORDING,
            CallState.ENDING,
            CallState.ENDED
        },
        CallState.ON_HOLD: {
            CallState.CONNECTED,
            CallState.ENDING,
            CallState.ENDED
        },
        CallState.MUTED: {
            CallState.CONNECTED,
            CallState.ON_HOLD,
            CallState.ENDING,
            CallState.ENDED
        },
        CallState.TRANSFERRING: {
            CallState.CONNECTED,
            CallState.ENDED,
            CallState.FAILED
        },
        CallState.RECORDING: {
            CallState.CONNECTED,
            CallState.ON_HOLD,
            CallState.MUTED,
            CallState.ENDING,
            CallState.ENDED
        },
        CallState.ENDING: {
            CallState.ENDED
        },
        CallState.ENDED: set(),  # Terminal state
        CallState.FAILED: set()  # Terminal state
    }

    return new in valid_transitions.get(current, set())
