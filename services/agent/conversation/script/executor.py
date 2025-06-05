"""
Script flow executor for running conversations with directed node/edge flow control.
"""
from typing import Dict, Any, Optional, List, Tuple
import asyncio
from datetime import datetime

from models.internal.callcontext import CallContext
from services.agent.core import AgentCore, AgentResponse
from services.agent.conversation import ScriptConversationFlow
from services.llm.script.schema import ScriptSchema
from services.agent.conversation.script.handler import TransitionHandler


class ScriptFlowExecutor:
  """
  High-level script flow executor with node/edge-based direction control.

  This class combines the script flow management with transition handling
  to provide a comprehensive API for directed conversation flows.
  """

  def __init__(
      self,
      script_flow: ScriptConversationFlow,
      transition_handler: TransitionHandler,
      call_id: str
  ):
    """
    Initialize the script flow executor.

    Args:
        script_flow: The script conversation flow manager
        transition_handler: Handler for state transitions
        call_id: ID of the active call
    """
    self.script_flow = script_flow
    self.transition_handler = transition_handler
    self.call_id = call_id
    self.context = {
        "entities": {},
        "intents": {},
        "history": []
    }
    self.current_state = None

  async def initialize(self) -> bool:
    """
    Initialize the script flow executor.

    Returns:
        Whether initialization was successful
    """
    # Get current script state
    info = self.script_flow.get_active_script_info(self.call_id)
    if not info:
      return False

    self.current_state = info.get("current_state")
    return self.current_state is not None

  async def process_turn(
      self,
      call_context: CallContext,
      user_input: str,
      metadata: Optional[Dict[str, Any]] = None
  ) -> Tuple[Optional[AgentResponse], Optional[str]]:
    """
    Process a conversation turn and determine next state.

    Args:
        call_context: The call context
        user_input: User's input text
        metadata: Additional metadata

    Returns:
        Tuple of (agent_response, next_state)
    """
    # Process turn with script flow
    response = await self.script_flow.process_script_turn(
        call_context, user_input, metadata
    )

    # Update conversation context
    await self._update_context(user_input, response)

    # Determine next state based on conversation
    next_state = None
    if self.current_state:
      next_state = self.transition_handler.determine_next_state(
          self.current_state, user_input, self.context
      )

    return response, next_state

  async def transition_if_needed(self, next_state: Optional[str]) -> bool:
    """
    Transition to the next state if needed.

    Args:
        next_state: The state to transition to, or None

    Returns:
        Whether a transition occurred
    """
    if not next_state or next_state == self.current_state:
      return False

    # Perform the transition
    success = await self.script_flow.transition_script_state(
        self.call_id, next_state
    )

    if success:
      self.current_state = next_state

    return success

  async def _update_context(
      self,
      user_input: str,
      response: Optional[AgentResponse]
  ) -> None:
    """
    Update the conversation context with latest turn.

    Args:
        user_input: User's input text
        response: Agent's response
    """
    # Add to conversation history
    self.context["history"].append({
        "user": user_input,
        "agent": response.text if response else "",
        "timestamp": datetime.now().isoformat(),
        "state": self.current_state
    })

    # Simple entity extraction
    entities = self._extract_entities(user_input)
    if entities:
      self.context["entities"].update(entities)

    # Simple intent detection
    intents = self._detect_intents(user_input)
    if intents:
      self.context["intents"] = intents

  def _extract_entities(self, text: str) -> Dict[str, Any]:
    """Simple entity extraction from text."""
    entities = {}
    text = text.lower()

    # Extremely simplified entity extraction
    if "name is " in text:
      name_part = text.split("name is ")[1].split(".")[0].strip()
      entities["name"] = name_part

    if "appointment for " in text:
      reason_part = text.split("appointment for ")[1].split(".")[0].strip()
      entities["reason"] = reason_part

    if "on " in text and any(day in text for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]):
      for day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        if day in text:
          entities["date"] = day
          break

    if "at " in text and any(str(hour) in text for hour in range(1, 13)):
      for hour in range(1, 13):
        if f" {hour} " in text or f" {hour}:" in text:
          if "pm" in text:
            entities["time"] = f"{hour}:00 PM"
          else:
            entities["time"] = f"{hour}:00 AM"
          break

    if "email" in text and "@" in text:
      # Simple regex to find email
      import re
      email_match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
      if email_match:
        entities["email"] = email_match.group(0)
        entities["contact_method"] = "email"
        entities["contact_info"] = email_match.group(0)

    if "phone" in text and any(char.isdigit() for char in text):
      # Extract phone numbers
      import re
      phone_match = re.search(
          r'(\d{3}[-.\s]??\d{3}[-.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-.\s]??\d{4}|\d{10})', text)
      if phone_match:
        entities["phone"] = phone_match.group(0)
        entities["contact_method"] = "phone"
        entities["contact_info"] = phone_match.group(0)

    return entities

  def _detect_intents(self, text: str) -> Dict[str, float]:
    """Simple keyword-based intent detection."""
    intents = {
        "schedule": 0.0,
        "reschedule": 0.0,
        "cancel": 0.0,
        "confirm": 0.0,
        "deny": 0.0
    }

    text = text.lower()

    # Simple keyword matching
    if any(word in text for word in ["schedule", "appointment", "book", "reserve"]):
      intents["schedule"] = 0.8

    if any(word in text for word in ["reschedule", "different", "another", "change"]):
      intents["reschedule"] = 0.8

    if any(word in text for word in ["cancel", "nevermind", "forget", "stop"]):
      intents["cancel"] = 0.8

    if any(word in text for word in ["yes", "correct", "right", "sure", "okay"]):
      intents["confirm"] = 0.9

    if any(word in text for word in ["no", "wrong", "incorrect", "not"]):
      intents["deny"] = 0.9

    return intents

  async def complete(self) -> None:
    """Complete and clean up the script flow."""
    await self.script_flow.deactivate_script_flow(self.call_id)
