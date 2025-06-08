"""
Agent initialization and personality management.
"""
import time
from typing import Dict, Any, Optional

from core.logging.setup import get_logger
from models.internal.callcontext import CallContext

logger = get_logger(__name__)


class InitializationManager:
  """Manages agent initialization and personality loading."""

  def __init__(self, agent_config: Any, context_memory: Dict[str, Any]):
    """Initialize the initialization manager."""
    self.config = agent_config
    self.context_memory = context_memory

  async def initialize_agent(self, call_context: CallContext):
    """
    Initialize agent for a new call.

    Args:
        call_context: Call context information
    """
    try:
      logger.info(f"Initializing agent for call: {call_context.call_id}")

      # Set up basic context
      self.context_memory.update({
          "call_start_time": time.time(),
          "phone_number": call_context.phone_number,
          "direction": call_context.direction,
          "call_id": call_context.call_id
      })

      # Load agent personality and instructions
      await self._load_agent_personality()

      logger.info("Agent initialized successfully")

    except Exception as e:
      logger.error(f"Error initializing agent: {str(e)}")
      raise

  async def _load_agent_personality(self):
    """Load agent personality and behavior from config."""
    try:
      # Extract personality traits from agent config
      personality_config = self.config.config.get("personality", {})

      self.context_memory.update({
          "agent_name": self.config.name,
          "agent_role": personality_config.get("role", "assistant"),
          "personality_traits": personality_config.get("traits", []),
          "conversation_style": personality_config.get("style", "professional"),
          "knowledge_base": personality_config.get("knowledge_base", []),
          "capabilities": personality_config.get("capabilities", [])
      })

      logger.info(f"Loaded personality for agent: {self.config.name}")

    except Exception as e:
      logger.warning(f"Error loading agent personality: {str(e)}")
