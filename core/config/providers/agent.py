"""
Agent configuration provider.
"""
import os
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class AgentConfig:
  """Agent configuration."""

  default_agent_id: str
  max_concurrent_calls_per_agent: int
  default_agent_timeout: int
  default_call_duration_limit: int
  max_total_concurrent_calls: int
  max_agents: int

  def __init__(self):
    """Initialize agent configuration from environment variables."""
    self.default_agent_id = os.getenv("DEFAULT_AGENT_ID", "agent_default")
    self.max_concurrent_calls_per_agent = int(
        os.getenv("MAX_CONCURRENT_CALLS_PER_AGENT", "3"))
    self.default_agent_timeout = int(os.getenv("DEFAULT_AGENT_TIMEOUT", "300"))
    self.default_call_duration_limit = int(
        os.getenv("DEFAULT_CALL_DURATION_LIMIT", "1800"))
    self.max_total_concurrent_calls = int(
        os.getenv("MAX_TOTAL_CONCURRENT_CALLS", "100"))
    self.max_agents = int(os.getenv("MAX_AGENTS", "5"))

  def to_dict(self) -> dict:
    """Convert to dictionary."""
    return {
        "default_agent_id": self.default_agent_id,
        "max_concurrent_calls_per_agent": self.max_concurrent_calls_per_agent,
        "default_agent_timeout": self.default_agent_timeout,
        "default_call_duration_limit": self.default_call_duration_limit,
        "max_total_concurrent_calls": self.max_total_concurrent_calls,
        "max_agents": self.max_agents
    }

  def reload(self):
    """Reload configuration from environment variables."""
    self.__init__()
