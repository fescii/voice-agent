"""Call state tracker for monitoring call metrics and analytics."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from pydantic import BaseModel

from core.logging.setup import get_logger
from .manager import CallState, CallStateInfo


class CallMetrics(BaseModel):
  """Call metrics model."""

  call_id: str
  total_duration: Optional[timedelta] = None
  connected_duration: Optional[timedelta] = None
  hold_duration: Optional[timedelta] = None
  mute_duration: Optional[timedelta] = None
  state_transitions: List[Dict] = []
  start_time: Optional[datetime] = None
  end_time: Optional[datetime] = None


class CallStateTracker:
  """Tracks call state changes for metrics and analytics."""

  def __init__(self):
    self.logger = get_logger(__name__)
    self._call_metrics: Dict[str, CallMetrics] = {}
    self._state_timers: Dict[str, Dict[str, datetime]] = {}

  async def start_tracking(self, call_id: str) -> None:
    """Start tracking a call."""

    self.logger.info(f"Starting tracking for call: {call_id}")

    self._call_metrics[call_id] = CallMetrics(
        call_id=call_id,
        start_time=datetime.now(timezone.utc),
        state_transitions=[]
    )
    self._state_timers[call_id] = {}

  async def track_state_change(self, state_info: CallStateInfo) -> None:
    """Track a state change event."""

    call_id = state_info.call_id

    if call_id not in self._call_metrics:
      await self.start_tracking(call_id)

    metrics = self._call_metrics[call_id]

    # Record state transition
    transition = {
        "from_state": state_info.previous_state,
        "to_state": state_info.state,
        "timestamp": state_info.timestamp,
        "metadata": state_info.metadata
    }
    metrics.state_transitions.append(transition)

    # Handle timing for specific states
    await self._update_state_timing(call_id, state_info)

    # Check if call ended
    if state_info.state in [CallState.ENDED, CallState.FAILED]:
      await self._finalize_metrics(call_id)

  async def get_metrics(self, call_id: str) -> Optional[CallMetrics]:
    """Get metrics for a call."""
    return self._call_metrics.get(call_id)

  async def get_active_metrics(self) -> Dict[str, CallMetrics]:
    """Get metrics for all active calls."""
    active_metrics = {}

    for call_id, metrics in self._call_metrics.items():
      if metrics.end_time is None:
        active_metrics[call_id] = metrics

    return active_metrics

  async def stop_tracking(self, call_id: str) -> Optional[CallMetrics]:
    """Stop tracking a call and return final metrics."""

    if call_id in self._call_metrics:
      metrics = self._call_metrics[call_id]

      # Finalize if not already done
      if metrics.end_time is None:
        await self._finalize_metrics(call_id)

      # Clean up
      final_metrics = self._call_metrics.pop(call_id, None)
      self._state_timers.pop(call_id, None)

      self.logger.info(f"Stopped tracking for call: {call_id}")

      return final_metrics

    return None

  async def _update_state_timing(self, call_id: str, state_info: CallStateInfo) -> None:
    """Update timing information for state changes."""

    current_time = state_info.timestamp
    state_timers = self._state_timers[call_id]

    # End previous state timing
    if state_info.previous_state:
      prev_state_key = f"{state_info.previous_state}_start"
      if prev_state_key in state_timers:
        start_time = state_timers[prev_state_key]
        duration = current_time - start_time

        # Update metrics based on state
        await self._add_state_duration(call_id, state_info.previous_state, duration)

        # Remove the timer
        del state_timers[prev_state_key]

    # Start new state timing
    state_key = f"{state_info.state}_start"
    state_timers[state_key] = current_time

  async def _add_state_duration(
      self,
      call_id: str,
      state: CallState,
      duration: timedelta
  ) -> None:
    """Add duration to specific state metrics."""

    metrics = self._call_metrics[call_id]

    if state == CallState.CONNECTED:
      if metrics.connected_duration is None:
        metrics.connected_duration = duration
      else:
        metrics.connected_duration += duration

    elif state == CallState.ON_HOLD:
      if metrics.hold_duration is None:
        metrics.hold_duration = duration
      else:
        metrics.hold_duration += duration

    elif state == CallState.MUTED:
      if metrics.mute_duration is None:
        metrics.mute_duration = duration
      else:
        metrics.mute_duration += duration

  async def _finalize_metrics(self, call_id: str) -> None:
    """Finalize metrics when call ends."""

    metrics = self._call_metrics[call_id]

    if metrics.end_time is None:
      metrics.end_time = datetime.now(timezone.utc)

    if metrics.start_time and metrics.end_time:
      metrics.total_duration = metrics.end_time - metrics.start_time

    # Finalize any ongoing state timings
    state_timers = self._state_timers.get(call_id, {})
    for timer_key, start_time in state_timers.items():
      if timer_key.endswith("_start"):
        state_name = timer_key.replace("_start", "")
        try:
          state = CallState(state_name)
          duration = metrics.end_time - start_time
          await self._add_state_duration(call_id, state, duration)
        except ValueError:
          # Invalid state name, skip
          pass

    self.logger.info(f"Finalized metrics for call: {call_id}")

  async def get_call_summary(self, call_id: str) -> Optional[Dict]:
    """Get a summary of call metrics."""

    metrics = await self.get_metrics(call_id)
    if not metrics:
      return None

    summary = {
        "call_id": call_id,
        "total_duration_seconds": (
            metrics.total_duration.total_seconds()
            if metrics.total_duration else None
        ),
        "connected_duration_seconds": (
            metrics.connected_duration.total_seconds()
            if metrics.connected_duration else None
        ),
        "hold_duration_seconds": (
            metrics.hold_duration.total_seconds()
            if metrics.hold_duration else None
        ),
        "mute_duration_seconds": (
            metrics.mute_duration.total_seconds()
            if metrics.mute_duration else None
        ),
        "state_transitions_count": len(metrics.state_transitions),
        "start_time": metrics.start_time,
        "end_time": metrics.end_time
    }

    return summary
