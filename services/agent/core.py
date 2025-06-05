"""
Core agent logic and decision-making engine.
"""

import asyncio
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import time

from core.logging.setup import get_logger
from models.internal.callcontext import CallContext
from services.llm.orchestrator import LLMOrchestrator
from data.db.models.agentconfig import AgentConfig

logger = get_logger(__name__)


class AgentState(Enum):
  """Agent states during conversation."""
  IDLE = "idle"
  LISTENING = "listening"
  THINKING = "thinking"
  SPEAKING = "speaking"
  WAITING = "waiting"
  ERROR = "error"


@dataclass
class AgentResponse:
  """Agent response structure."""
  text: str
  audio_data: Optional[bytes] = None
  action: Optional[str] = None
  confidence: float = 1.0
  thinking_time: float = 0.0
  metadata: Optional[Dict[str, Any]] = None


class AgentCore:
  """Core agent logic and conversation engine."""

  def __init__(
      self,
      agent_config: AgentConfig,
      llm_orchestrator: LLMOrchestrator
  ):
    """Initialize agent core."""
    self.config = agent_config
    self.llm_orchestrator = llm_orchestrator
    self.state = AgentState.IDLE
    self.conversation_history = []
    self.context_memory = {}
    self.current_call_context: Optional[CallContext] = None

  async def initialize(self, call_context: CallContext):
    """
    Initialize agent for a new call.

    Args:
        call_context: Call context information
    """
    try:
      logger.info(f"Initializing agent for call: {call_context.call_id}")

      self.current_call_context = call_context
      self.state = AgentState.IDLE
      self.conversation_history = []
      self.context_memory = {
          "call_start_time": time.time(),
          "caller_info": call_context.caller_info,
          "call_type": call_context.call_type
      }

      # Load agent personality and instructions
      await self._load_agent_personality()

      logger.info("Agent initialized successfully")

    except Exception as e:
      logger.error(f"Error initializing agent: {str(e)}")
      self.state = AgentState.ERROR
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

  async def process_user_input(
      self,
      user_text: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> AgentResponse:
    """
    Process user input and generate agent response.

    Args:
        user_text: Transcribed user speech
        audio_data: Original audio data
        metadata: Additional metadata

    Returns:
        Agent response
    """
    try:
      start_time = time.time()
      self.state = AgentState.THINKING

      logger.info(f"Processing user input: '{user_text[:100]}...'")

      # Add user input to conversation history
      self.conversation_history.append({
          "role": "user",
          "content": user_text,
          "timestamp": time.time(),
          "metadata": metadata or {}
      })

      # Generate context for LLM
      context = await self._build_conversation_context()

      # Get LLM response
      llm_response = await self.llm_orchestrator.generate_response(
          messages=context["messages"],
          context=context["metadata"],
          config=context["generation_config"]
      )

      # Process LLM response
      agent_response = await self._process_llm_response(llm_response)

      # Add agent response to conversation history
      self.conversation_history.append({
          "role": "assistant",
          "content": agent_response.text,
          "timestamp": time.time(),
          "metadata": {
              "confidence": agent_response.confidence,
              "thinking_time": agent_response.thinking_time,
              "action": agent_response.action
          }
      })

      thinking_time = time.time() - start_time
      agent_response.thinking_time = thinking_time

      self.state = AgentState.IDLE

      logger.info(
          f"Generated response in {thinking_time:.2f}s: '{agent_response.text[:100]}...'")

      return agent_response

    except Exception as e:
      logger.error(f"Error processing user input: {str(e)}")
      self.state = AgentState.ERROR

      # Return error response
      return AgentResponse(
          text="I apologize, but I'm having trouble processing your request right now. Could you please try again?",
          confidence=0.0,
          thinking_time=time.time() - start_time
      )

  async def _build_conversation_context(self) -> Dict[str, Any]:
    """Build context for LLM generation."""
    try:
      # Create system message with agent personality
      system_message = await self._create_system_message()

      # Build conversation messages
      messages = [system_message]

      # Add recent conversation history (last 10 exchanges)
      recent_history = self.conversation_history[-20:]  # Last 20 messages
      messages.extend([
          {
              "role": msg["role"],
              "content": msg["content"]
          }
          for msg in recent_history
      ])

      # Build metadata context
      metadata = {
          "call_context": self.current_call_context.__dict__ if self.current_call_context else {},
          "agent_memory": self.context_memory,
          "conversation_length": len(self.conversation_history),
          "agent_state": self.state.value
      }

      # Generation configuration
      generation_config = {
          "temperature": self.config.config.get("temperature", 0.7),
          "max_tokens": self.config.config.get("max_tokens", 150),
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
      personality = self.context_memory.get("personality_traits", [])
      role = self.context_memory.get("agent_role", "assistant")
      style = self.context_memory.get("conversation_style", "professional")

      system_prompt = f"""You are {self.config.name}, a {role} AI voice assistant.

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
- Caller: {self.context_memory.get('caller_info', {}).get('name', 'Unknown')}
- Call type: {self.context_memory.get('call_type', 'unknown')}
- Call duration: {time.time() - self.context_memory.get('call_start_time', time.time()):.0f} seconds

Your capabilities: {', '.join(self.context_memory.get('capabilities', []))}
"""

      return {
          "role": "system",
          "content": system_prompt
      }

    except Exception as e:
      logger.error(f"Error creating system message: {str(e)}")
      return {
          "role": "system",
          "content": f"You are {self.config.name}, a helpful AI assistant."
      }

  async def _process_llm_response(self, llm_response: Dict[str, Any]) -> AgentResponse:
    """Process LLM response and extract actions."""
    try:
      response_text = llm_response.get("text", "").strip()
      confidence = llm_response.get("confidence", 1.0)

      # Extract any special actions or commands from response
      action = None
      if response_text.startswith("/"):
        # Command format: /action_name response_text
        parts = response_text.split(" ", 1)
        if len(parts) > 1:
          action = parts[0][1:]  # Remove leading /
          response_text = parts[1]

      # Clean up response text for speech
      response_text = self._clean_response_for_speech(response_text)

      return AgentResponse(
          text=response_text,
          action=action,
          confidence=confidence,
          metadata=llm_response.get("metadata", {})
      )

    except Exception as e:
      logger.error(f"Error processing LLM response: {str(e)}")
      return AgentResponse(
          text="I apologize, I didn't understand that completely. Could you please rephrase?",
          confidence=0.5
      )

  def _clean_response_for_speech(self, text: str) -> str:
    """Clean response text for natural speech synthesis."""
    # Remove markdown formatting
    text = text.replace("*", "").replace("_", "").replace("`", "")

    # Remove excessive punctuation
    text = text.replace("...", " pause ")

    # Ensure proper sentence ending
    if text and not text.endswith((".", "!", "?")):
      text += "."

    return text.strip()

  async def handle_call_action(self, action: str, params: Optional[Dict[str, Any]] = None) -> AgentResponse:
    """
    Handle call-specific actions.

    Args:
        action: Action to perform (transfer, hold, etc.)
        params: Action parameters

    Returns:
        Agent response acknowledging the action
    """
    try:
      logger.info(f"Handling call action: {action}")

      if action == "transfer":
        return await self._handle_transfer(params or {})
      elif action == "hold":
        return await self._handle_hold(params or {})
      elif action == "mute":
        return await self._handle_mute(params or {})
      elif action == "end_call":
        return await self._handle_end_call(params or {})
      else:
        return AgentResponse(
            text=f"I'm not sure how to perform the action: {action}",
            confidence=0.3
        )

    except Exception as e:
      logger.error(f"Error handling call action {action}: {str(e)}")
      return AgentResponse(
          text="I encountered an issue while trying to perform that action.",
          confidence=0.0
      )

  async def _handle_transfer(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle call transfer action."""
    target = params.get("target", "operator")
    return AgentResponse(
        text=f"I'll transfer you to {target} now. Please hold for a moment.",
        action="transfer",
        metadata=params
    )

  async def _handle_hold(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle call hold action."""
    return AgentResponse(
        text="I'll put you on hold for a moment. Please wait.",
        action="hold",
        metadata=params
    )

  async def _handle_mute(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle call mute action."""
    return AgentResponse(
        text="I'll mute the call now.",
        action="mute",
        metadata=params
    )

  async def _handle_end_call(self, params: Dict[str, Any]) -> AgentResponse:
    """Handle end call action."""
    return AgentResponse(
        text="Thank you for calling. Have a great day!",
        action="end_call",
        metadata=params
    )

  async def get_conversation_summary(self) -> Dict[str, Any]:
    """
    Get summary of current conversation.

    Returns:
        Conversation summary
    """
    try:
      total_exchanges = len(self.conversation_history) // 2
      call_duration = time.time() - self.context_memory.get("call_start_time", time.time())

      user_messages = [
          msg for msg in self.conversation_history if msg["role"] == "user"]
      agent_messages = [
          msg for msg in self.conversation_history if msg["role"] == "assistant"]

      summary = {
          "call_id": self.current_call_context.call_id if self.current_call_context else None,
          "agent_name": self.config.name,
          "total_exchanges": total_exchanges,
          "call_duration": call_duration,
          "user_message_count": len(user_messages),
          "agent_message_count": len(agent_messages),
          "current_state": self.state.value,
          "avg_response_time": sum(
              msg.get("metadata", {}).get("thinking_time", 0)
              for msg in agent_messages
          ) / max(len(agent_messages), 1),
          "conversation_topics": await self._extract_topics()
      }

      return summary

    except Exception as e:
      logger.error(f"Error generating conversation summary: {str(e)}")
      return {"error": str(e)}

  async def _extract_topics(self) -> List[str]:
    """Extract main topics from conversation."""
    # Simple keyword extraction - could be enhanced with NLP
    try:
      all_text = " ".join([
          msg["content"]
          for msg in self.conversation_history
          if msg["role"] == "user"
      ]).lower()

      # Basic topic keywords
      topic_keywords = {
          "support": ["help", "problem", "issue", "trouble"],
          "sales": ["buy", "purchase", "price", "cost", "product"],
          "billing": ["bill", "payment", "charge", "invoice"],
          "account": ["account", "profile", "settings", "login"],
          "technical": ["not working", "error", "bug", "technical"]
      }

      detected_topics = []
      for topic, keywords in topic_keywords.items():
        if any(keyword in all_text for keyword in keywords):
          detected_topics.append(topic)

      return detected_topics or ["general"]

    except Exception as e:
      logger.warning(f"Error extracting topics: {str(e)}")
      return ["general"]

  def get_current_state(self) -> AgentState:
    """Get current agent state."""
    return self.state

  def set_state(self, state: AgentState):
    """Set agent state."""
    logger.debug(f"Agent state changed: {self.state.value} -> {state.value}")
    self.state = state
