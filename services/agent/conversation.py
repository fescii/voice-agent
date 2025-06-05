"""
Conversation management and flow control.
"""

import asyncio
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass
import time

from core.logging.setup import get_logger
from .core import AgentCore, AgentResponse, AgentState

logger = get_logger(__name__)


class ConversationFlow(Enum):
  """Conversation flow states."""
  GREETING = "greeting"
  GATHERING_INFO = "gathering_info"
  PROCESSING_REQUEST = "processing_request"
  PROVIDING_SOLUTION = "providing_solution"
  CONFIRMING = "confirming"
  CLOSING = "closing"
  ERROR_HANDLING = "error_handling"


@dataclass
class ConversationTurn:
  """Single conversation turn."""
  user_input: str
  agent_response: str
  timestamp: float
  flow_state: ConversationFlow
  confidence: float
  metadata: Dict[str, Any]


class ConversationManager:
  """Manages conversation flow and state transitions."""

  def __init__(self, agent_core: AgentCore):
    """Initialize conversation manager."""
    self.agent_core = agent_core
    self.current_flow = ConversationFlow.GREETING
    self.conversation_turns: List[ConversationTurn] = []
    self.conversation_context = {}
    self.flow_handlers = {}
    self.error_count = 0
    self.max_errors = 3

    # Register flow handlers
    self._register_flow_handlers()

  def _register_flow_handlers(self):
    """Register handlers for different conversation flows."""
    self.flow_handlers = {
        ConversationFlow.GREETING: self._handle_greeting,
        ConversationFlow.GATHERING_INFO: self._handle_gathering_info,
        ConversationFlow.PROCESSING_REQUEST: self._handle_processing_request,
        ConversationFlow.PROVIDING_SOLUTION: self._handle_providing_solution,
        ConversationFlow.CONFIRMING: self._handle_confirming,
        ConversationFlow.CLOSING: self._handle_closing,
        ConversationFlow.ERROR_HANDLING: self._handle_error
    }

  async def process_conversation_turn(
      self,
      user_input: str,
      audio_data: Optional[bytes] = None,
      metadata: Optional[Dict[str, Any]] = None
  ) -> AgentResponse:
    """
    Process a conversation turn with flow management.

    Args:
        user_input: User's spoken input (transcribed)
        audio_data: Original audio data
        metadata: Additional metadata

    Returns:
        Agent response with flow management
    """
    try:
      logger.info(
          f"Processing conversation turn in flow: {self.current_flow.value}")

      # Get base response from agent core
      base_response = await self.agent_core.process_user_input(
          user_input, audio_data, metadata
      )

      # Apply flow-specific processing
      flow_response = await self._apply_flow_processing(
          user_input, base_response, metadata or {}
      )

      # Record conversation turn
      turn = ConversationTurn(
          user_input=user_input,
          agent_response=flow_response.text,
          timestamp=time.time(),
          flow_state=self.current_flow,
          confidence=flow_response.confidence,
          metadata=metadata or {}
      )
      self.conversation_turns.append(turn)

      # Update conversation context
      await self._update_conversation_context(user_input, flow_response)

      # Determine next flow state
      await self._determine_next_flow(user_input, flow_response)

      # Reset error count on successful processing
      self.error_count = 0

      logger.info(
          f"Conversation turn completed. Next flow: {self.current_flow.value}")

      return flow_response

    except Exception as e:
      logger.error(f"Error processing conversation turn: {str(e)}")

      self.error_count += 1
      if self.error_count >= self.max_errors:
        self.current_flow = ConversationFlow.ERROR_HANDLING

      return AgentResponse(
          text="I'm having some difficulty understanding. Could you please repeat that?",
          confidence=0.3
      )

  async def _apply_flow_processing(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Apply flow-specific processing to the response."""
    try:
      handler = self.flow_handlers.get(self.current_flow)

      if handler:
        return await handler(user_input, base_response, metadata)
      else:
        logger.warning(f"No handler for flow: {self.current_flow.value}")
        return base_response

    except Exception as e:
      logger.error(f"Error in flow processing: {str(e)}")
      return base_response

  async def _handle_greeting(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Handle greeting flow."""
    # Check if this is the first interaction
    if len(self.conversation_turns) == 0:
      greeting_text = await self._generate_personalized_greeting()
      return AgentResponse(
          text=greeting_text,
          confidence=1.0,
          metadata={"flow": "greeting", "personalized": True}
      )

    # Add welcoming elements to response
    enhanced_text = self._add_welcoming_tone(base_response.text)

    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**base_response.metadata or {}, "flow": "greeting"}
    )

  async def _handle_gathering_info(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Handle information gathering flow."""
    # Extract information from user input
    extracted_info = await self._extract_information(user_input)

    # Update conversation context with extracted info
    self.conversation_context.update(extracted_info)

    # Check if we have enough information
    if await self._has_sufficient_information():
      # Move to processing
      self.current_flow = ConversationFlow.PROCESSING_REQUEST
      enhanced_text = "Thank you for that information. Let me help you with that."
    else:
      # Ask for more information
      missing_info = await self._identify_missing_information()
      enhanced_text = f"{base_response.text} Could you also tell me about {missing_info}?"

    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        metadata={**base_response.metadata or {}, "flow": "gathering_info", "extracted_info": extracted_info}
    )

  async def _handle_processing_request(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Handle request processing flow."""
    # Add processing indicators
    processing_prefixes = [
        "Let me look into that for you.",
        "I'm checking on that now.",
        "Let me find the best solution for you."
    ]

    # Use confidence to select appropriate prefix
    if base_response.confidence > 0.8:
      prefix = processing_prefixes[0]
    elif base_response.confidence > 0.5:
      prefix = processing_prefixes[1]
    else:
      prefix = processing_prefixes[2]

    enhanced_text = f"{prefix} {base_response.text}"

    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**base_response.metadata or {}, "flow": "processing_request"}
    )

  async def _handle_providing_solution(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Handle solution providing flow."""
    # Add solution framing
    solution_intro = "Here's what I can do to help: "
    enhanced_text = f"{solution_intro}{base_response.text}"

    # Add follow-up question
    follow_up = " Does this solution work for you?"
    enhanced_text += follow_up

    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**base_response.metadata or {}, "flow": "providing_solution"}
    )

  async def _handle_confirming(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Handle confirmation flow."""
    # Check for confirmation/rejection in user input
    is_confirmed = await self._detect_confirmation(user_input)

    if is_confirmed:
      enhanced_text = "Great! I'll proceed with that. " + base_response.text
      # Move to closing or back to processing
      self.current_flow = ConversationFlow.CLOSING
    else:
      enhanced_text = "I understand. Let me try a different approach. " + base_response.text
      # Go back to gathering info or processing
      self.current_flow = ConversationFlow.GATHERING_INFO

    return AgentResponse(
        text=enhanced_text,
        confidence=base_response.confidence,
        metadata={**base_response.metadata or {}, "flow": "confirming", "confirmed": is_confirmed}
    )

  async def _handle_closing(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Handle closing flow."""
    # Add closing elements
    closing_text = base_response.text

    if not any(phrase in closing_text.lower() for phrase in ["thank", "goodbye", "bye"]):
      closing_text += " Thank you for calling. Is there anything else I can help you with?"

    return AgentResponse(
        text=closing_text,
        confidence=base_response.confidence,
        action=base_response.action,
        metadata={**base_response.metadata or {}, "flow": "closing"}
    )

  async def _handle_error(
      self,
      user_input: str,
      base_response: AgentResponse,
      metadata: Dict[str, Any]
  ) -> AgentResponse:
    """Handle error flow."""
    error_responses = [
        "I apologize for the confusion. Let me transfer you to a human agent who can better assist you.",
        "I'm having trouble understanding your request. Would you like to speak with a human representative?",
        "Let me connect you with one of our specialists who can help you better."
    ]

    error_text = error_responses[min(
        self.error_count - 1, len(error_responses) - 1)]

    return AgentResponse(
        text=error_text,
        confidence=0.2,
        action="transfer",
        metadata={"flow": "error_handling", "error_count": self.error_count}
    )

  async def _generate_personalized_greeting(self) -> str:
    """Generate a personalized greeting."""
    greetings = [
        f"Hello! I'm {self.agent_core.config.name}, and I'm here to help you today.",
        f"Hi there! This is {self.agent_core.config.name}. How can I assist you?",
        f"Good day! I'm {self.agent_core.config.name}, your AI assistant. What can I help you with?"
    ]

    # Could be enhanced with time-based greetings, caller history, etc.
    return greetings[0]

  def _add_welcoming_tone(self, text: str) -> str:
    """Add welcoming tone to response."""
    welcoming_phrases = ["I'm happy to help with that.",
                         "I'd be glad to assist you.", "Let me help you with that."]

    if not any(phrase in text.lower() for phrase in ["happy", "glad", "help"]):
      return f"{welcoming_phrases[0]} {text}"

    return text

  async def _extract_information(self, user_input: str) -> Dict[str, Any]:
    """Extract structured information from user input."""
    # Simple keyword-based extraction
    # In production, this could use NLP/NER

    extracted = {}

    # Extract contact information
    import re

    # Phone numbers
    phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    phones = re.findall(phone_pattern, user_input)
    if phones:
      extracted["phone"] = phones[0]

    # Email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, user_input)
    if emails:
      extracted["email"] = emails[0]

    # Account numbers (simple pattern)
    account_pattern = r'\b(?:account|acct)\s*(?:number|#)?\s*:?\s*([A-Za-z0-9]+)\b'
    accounts = re.findall(account_pattern, user_input, re.IGNORECASE)
    if accounts:
      extracted["account_number"] = accounts[0]

    return extracted

  async def _has_sufficient_information(self) -> bool:
    """Check if we have sufficient information to proceed."""
    # Define required information based on conversation context
    required_fields = ["contact_reason"]  # Basic requirement

    # Check if we have enough context
    return len(self.conversation_context) >= len(required_fields)

  async def _identify_missing_information(self) -> str:
    """Identify what information is still needed."""
    # Simple implementation - could be more sophisticated
    if "contact_reason" not in self.conversation_context:
      return "what you're calling about"
    elif "account_number" not in self.conversation_context:
      return "your account number"
    else:
      return "more details"

  async def _detect_confirmation(self, user_input: str) -> bool:
    """Detect confirmation or rejection in user input."""
    confirmation_words = ["yes", "yeah", "yep",
                          "correct", "right", "exactly", "proceed"]
    rejection_words = ["no", "nope", "wrong", "incorrect", "different"]

    user_lower = user_input.lower()

    has_confirmation = any(word in user_lower for word in confirmation_words)
    has_rejection = any(word in user_lower for word in rejection_words)

    # If both or neither, default to confirmation
    if has_confirmation and not has_rejection:
      return True
    elif has_rejection and not has_confirmation:
      return False
    else:
      return True  # Default to positive

  async def _determine_next_flow(self, user_input: str, response: AgentResponse):
    """Determine the next conversation flow state."""
    try:
      current_turn_count = len(self.conversation_turns)

      # Flow transition logic
      if self.current_flow == ConversationFlow.GREETING:
        if current_turn_count >= 1:
          self.current_flow = ConversationFlow.GATHERING_INFO

      elif self.current_flow == ConversationFlow.GATHERING_INFO:
        if await self._has_sufficient_information():
          self.current_flow = ConversationFlow.PROCESSING_REQUEST

      elif self.current_flow == ConversationFlow.PROCESSING_REQUEST:
        if response.action or response.confidence > 0.8:
          self.current_flow = ConversationFlow.PROVIDING_SOLUTION

      elif self.current_flow == ConversationFlow.PROVIDING_SOLUTION:
        self.current_flow = ConversationFlow.CONFIRMING

      elif self.current_flow == ConversationFlow.CONFIRMING:
        # Handled in _handle_confirming
        pass

      elif self.current_flow == ConversationFlow.CLOSING:
        # Check if user wants to continue
        continue_indicators = ["more", "another", "also", "else"]
        if any(indicator in user_input.lower() for indicator in continue_indicators):
          self.current_flow = ConversationFlow.GATHERING_INFO

    except Exception as e:
      logger.error(f"Error determining next flow: {str(e)}")

  async def _update_conversation_context(self, user_input: str, response: AgentResponse):
    """Update conversation context with new information."""
    try:
      # Extract and store key information
      extracted_info = await self._extract_information(user_input)
      self.conversation_context.update(extracted_info)

      # Store response metadata
      if response.metadata:
        self.conversation_context.update(response.metadata)

    except Exception as e:
      logger.warning(f"Error updating conversation context: {str(e)}")

  def get_conversation_flow(self) -> ConversationFlow:
    """Get current conversation flow."""
    return self.current_flow

  def set_conversation_flow(self, flow: ConversationFlow):
    """Set conversation flow."""
    logger.info(
        f"Conversation flow changed: {self.current_flow.value} -> {flow.value}")
    self.current_flow = flow

  async def get_conversation_stats(self) -> Dict[str, Any]:
    """Get conversation statistics."""
    return {
        "current_flow": self.current_flow.value,
        "total_turns": len(self.conversation_turns),
        "average_confidence": sum(turn.confidence for turn in self.conversation_turns) / max(len(self.conversation_turns), 1),
        "conversation_context": self.conversation_context,
        "error_count": self.error_count,
        "flows_visited": list(set(turn.flow_state.value for turn in self.conversation_turns))
    }
