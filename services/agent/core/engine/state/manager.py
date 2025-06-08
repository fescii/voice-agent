"""
State management for agent engine.
"""
from core.logging.setup import get_logger
from ...state import AgentState

logger = get_logger(__name__)


class StateManager:
  """Manages agent state transitions and tracking."""

  def __init__(self, agent_core):
    """Initialize the state manager."""
    self.agent_core = agent_core

  def get_current_state(self) -> AgentState:
    """Get current agent state."""
    return self.agent_core.state

  def set_state(self, state: AgentState):
    """Set agent state."""
    logger.debug(
        f"Agent state changed: {self.agent_core.state.value} -> {state.value}")
    self.agent_core.state = state
