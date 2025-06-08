"""
Context management and conversation building.
"""
import time
from typing import Dict, Any, Optional

from core.logging.setup import get_logger

logger = get_logger(__name__)


class ContextManager:
  """Manages conversation context and system message creation."""

  def __init__(self, agent_core):
    """Initialize the context manager."""
    self.agent_core = agent_core

  async def build_conversation_context(self) -> Dict[str, Any]:
    """Build context for LLM generation."""
    try:
      # Create system message with agent personality
      system_message = await self._create_system_message()

      # Build conversation messages
      messages = [system_message]

      # Add recent conversation history (last 10 exchanges)
      # Last 20 messages
      recent_history = self.agent_core.conversation_history[-20:]
      messages.extend([
          {
              "role": msg["role"],
              "content": msg["content"]
          }
          for msg in recent_history
      ])

      # Build metadata context
      metadata = {
          "call_context": self.agent_core.current_call_context.__dict__ if self.agent_core.current_call_context else {},
          "agent_memory": self.agent_core.context_memory,
          "conversation_length": len(self.agent_core.conversation_history),
          "agent_state": self.agent_core.state.value
      }

      # Generation configuration
      generation_config = {
          "temperature": self.agent_core.config.config.get("temperature", 0.7),
          "max_tokens": self.agent_core.config.config.get("max_tokens", 150),
          "response_format": "text"
      }

      return {
          "messages": messages,
          "metadata": metadata,
          "generation_config": generation_config
      }

    except Exception as e:
      logger.error(f"Error building conversation context: {str(e)}")
      raise

  async def _create_system_message(self) -> Dict[str, str]:
    """Create system message with agent personality and instructions."""
    try:
      personality = self.agent_core.context_memory.get(
          "personality_traits", [])
      role = self.agent_core.context_memory.get("agent_role", "assistant")
      style = self.agent_core.context_memory.get(
          "conversation_style", "professional")

      system_prompt = f"""You are {self.agent_core.config.name}, a {role} AI voice assistant.

Personality traits: {', '.join(personality)}
Conversation style: {style}

Guidelines:
- Keep responses concise and natural for voice conversation
- Be helpful, accurate, and engaging
- Maintain a {style} tone throughout the conversation
- Ask clarifying questions when needed
- Remember context from the conversation
- Respond in a way that flows naturally in speech

Current call context:
- Phone: {self.agent_core.context_memory.get('phone_number', 'Unknown')}
- Direction: {self.agent_core.context_memory.get('direction', 'unknown')}
- Call duration: {time.time() - self.agent_core.context_memory.get('call_start_time', time.time()):.0f} seconds

Your capabilities: {', '.join(self.agent_core.context_memory.get('capabilities', []))}
"""

      return {
          "role": "system",
          "content": system_prompt
      }

    except Exception as e:
      logger.error(f"Error creating system message: {str(e)}")
      return {
          "role": "system",
          "content": f"You are {self.agent_core.config.name}, a helpful AI assistant."
      }
