"""
High-level agent service for managing AI agents.
"""
import time
from typing import Dict, Any, Optional
from core.logging.setup import get_logger
from data.db.models.agentconfig import AgentConfig
from .engine import AgentCore

logger = get_logger(__name__)


class AgentService:
  """High-level service for managing AI agents."""

  def __init__(self):
    """Initialize agent service."""
    self.logger = logger
    self.active_agents = {}

  async def create_agent(self, agent_id: str, config: AgentConfig) -> bool:
    """Create and initialize an agent."""
    try:
      # Import here to avoid circular imports
      from services.llm.orchestrator import LLMOrchestrator

      llm_orchestrator = LLMOrchestrator()
      agent_core = AgentCore(config, llm_orchestrator)

      self.active_agents[agent_id] = {
          'core': agent_core,
          'config': config,
          'created_at': time.time()
      }

      self.logger.info(f"Created agent {agent_id}")
      return True

    except Exception as e:
      self.logger.error(f"Failed to create agent {agent_id}: {e}")
      return False

  async def get_agent(self, agent_id: str) -> Optional[AgentCore]:
    """Get an agent by ID."""
    agent_info = self.active_agents.get(agent_id)
    return agent_info['core'] if agent_info else None

  async def remove_agent(self, agent_id: str) -> bool:
    """Remove an agent."""
    try:
      if agent_id in self.active_agents:
        del self.active_agents[agent_id]
        self.logger.info(f"Removed agent {agent_id}")
      return True
    except Exception as e:
      self.logger.error(f"Failed to remove agent {agent_id}: {e}")
      return False

  async def process_message(self, agent_id: str, message: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Process a message with an agent."""
    try:
      agent = await self.get_agent(agent_id)
      if not agent:
        self.logger.warning(f"Agent {agent_id} not found")
        return None

      response = await agent.process_message(message, context)
      return response.text if response else None

    except Exception as e:
      self.logger.error(f"Failed to process message for agent {agent_id}: {e}")
      return None
