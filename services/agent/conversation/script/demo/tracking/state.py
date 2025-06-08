"""
State tracking for script-driven conversation flows.
"""

from typing import Dict, Any, Optional
from services.agent.conversation import ScriptConversationFlow


class ScriptStateTracker:
  """State tracker for advanced script examples."""

  def __init__(self, script_flow: ScriptConversationFlow, call_id: str):
    """
    Initialize the state tracker.

    Args:
        script_flow: The script flow manager
        call_id: The ID of the call to track
    """
    self.script_flow = script_flow
    self.call_id = call_id
    self.current_state = None
    self.collected_entities = {}

  async def track_state(self) -> Optional[Dict[str, Any]]:
    """
    Get current script state information.

    Returns:
        Script flow state information or None if not available
    """
    info = self.script_flow.get_active_script_info(self.call_id)
    if info:
      self.current_state = info.get("current_state")

    return info

  async def handle_transition(self, user_input: str) -> Optional[str]:
    """
    Determine next state based on user input and current state.

    Args:
        user_input: User's input text

    Returns:
        Next state name if a transition should occur
    """
    # Get current active script info
    info = await self.track_state()
    if not info:
      return None

    # Simple intent detection based on keywords
    intents = self._detect_intent(user_input)
    entities = self._extract_entities(user_input)

    # Update collected entities
    self.collected_entities.update(entities)

    # Basic state transition logic based on current state
    next_state = None

    # Example transition logic
    if self.current_state == "greeting":
      next_state = "collect_information"

    elif self.current_state == "collect_information":
      # Check if we have enough information to proceed
      required_entities = ["name", "date", "time", "reason"]
      if all(entity in self.collected_entities for entity in required_entities):
        next_state = "check_availability"

    elif self.current_state == "check_availability":
      # Simulate availability check
      if "not available" in user_input.lower():
        next_state = "reschedule"
      else:
        next_state = "confirm_details"

    elif self.current_state == "confirm_details":
      if any(word in user_input.lower() for word in ["yes", "correct", "right"]):
        next_state = "schedule_appointment"
      else:
        next_state = "collect_information"

    elif self.current_state == "schedule_appointment":
      next_state = "handle_confirmation_preference"

    elif self.current_state == "handle_confirmation_preference":
      next_state = "closing"

    elif self.current_state == "reschedule":
      if any(word in user_input.lower() for word in ["yes", "reschedule", "different"]):
        next_state = "collect_information"
      else:
        next_state = "closing"

    return next_state

  def _detect_intent(self, text: str) -> Dict[str, float]:
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

  def _extract_entities(self, text: str) -> Dict[str, Any]:
    """
    Simple entity extraction from text.

    Note: In a real system, this would use NLP/NER to extract entities.
    This is just a simple simulation for the example.
    """
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

    return entities
