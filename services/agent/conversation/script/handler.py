"""
Script flow transition handlers for node/edge traversal.
"""
from typing import Dict, Any, Optional, List
import re
from datetime import datetime, time

from services.llm.script.schema import ScriptSchema, Edge, State, EdgeCondition


class TransitionHandler:
  """Handles transitions between script states based on defined edges."""

  def __init__(self, script: ScriptSchema):
    """
    Initialize with a script.

    Args:
        script: The script schema containing states and edges
    """
    self.script = script
    self.states = {state.name: state for state in script.states}
    self.edges_by_source = self._organize_edges_by_source()

  def _organize_edges_by_source(self) -> Dict[str, List[Edge]]:
    """Organize edges by source state for efficient lookup."""
    result = {}
    for edge in self.script.edges:
      if edge.from_state not in result:
        result[edge.from_state] = []
      result[edge.from_state].append(edge)
    return result

  def get_possible_transitions(self, current_state: str) -> List[Edge]:
    """
    Get all possible transitions from the current state.

    Args:
        current_state: The name of the current state

    Returns:
        List of edges representing possible transitions
    """
    return self.edges_by_source.get(current_state, [])

  def determine_next_state(
      self,
      current_state: str,
      user_input: str,
      context: Dict[str, Any]
  ) -> Optional[str]:
    """
    Determine the next state based on user input and edge conditions.

    Args:
        current_state: Current state name
        user_input: User's input text
        context: Additional context with collected entities, etc.

    Returns:
        Next state name or None if no transition is appropriate
    """
    # Get possible transitions from current state
    possible_edges = self.get_possible_transitions(current_state)

    # If no edges, stay in current state
    if not possible_edges:
      return None

    # If only one edge and no condition, take that path
    if len(possible_edges) == 1 and not possible_edges[0].condition:
      return possible_edges[0].to_state

    # Evaluate conditions for all edges
    for edge in possible_edges:
      if not edge.condition:
        continue

      if self._evaluate_condition(edge.condition, user_input, context):
        return edge.to_state

    # If no conditions matched, but there's an edge without condition, use that
    for edge in possible_edges:
      if not edge.condition:
        return edge.to_state

    # No valid transition found
    return None

  def _evaluate_condition(
      self,
      condition: EdgeCondition,
      user_input: str,
      context: Dict[str, Any]
  ) -> bool:
    """
    Evaluate if a condition is met based on user input and context.

    Args:
        condition: The condition to evaluate
        user_input: User's input text
        context: Additional context information

    Returns:
        Whether the condition is met
    """
    # Entity completion condition
    if condition.type == "entity_complete":
      entities = context.get("entities", {})
      required_entities = condition.value if isinstance(
          condition.value, list) else [condition.value]

      if condition.operator == "all_present":
        return all(entity in entities for entity in required_entities)
      else:
        return any(entity in entities for entity in required_entities)

    # Intent detection condition
    elif condition.type == "intent":
      intents = context.get("intents", {})
      target_intent = condition.value
      intent_score = intents.get(target_intent, 0)

      # Default threshold
      threshold = 0.6

      if condition.operator == "equals":
        return intent_score >= threshold and intent_score == max(intents.values())
      elif condition.operator == "not_equals":
        return intent_score < threshold

    # Sentiment condition
    elif condition.type == "sentiment":
      # Simple keyword-based sentiment detection
      positive_words = ["yes", "good", "great",
                        "excellent", "happy", "agree", "correct"]
      negative_words = ["no", "bad", "wrong",
                        "incorrect", "disagree", "not", "don't"]

      word_tokens = set(re.findall(r'\b\w+\b', user_input.lower()))
      positive_count = len([w for w in word_tokens if w in positive_words])
      negative_count = len([w for w in word_tokens if w in negative_words])

      is_positive = positive_count > negative_count

      if condition.value is True and condition.operator == "equals":
        return is_positive
      elif condition.value is False and condition.operator == "equals":
        return not is_positive

    # Confirmation condition
    elif condition.type == "confirmation":
      # Simple confirmation detection
      affirmative = ["yes", "correct", "right",
                     "sure", "okay", "fine", "agree", "true"]
      negative = ["no", "wrong", "incorrect", "not", "disagree", "false"]

      words = set(re.findall(r'\b\w+\b', user_input.lower()))

      is_confirmed = any(word in words for word in affirmative) and not any(
          word in words for word in negative)

      if condition.value is True and condition.operator == "equals":
        return is_confirmed
      elif condition.value is False and condition.operator == "equals":
        return not is_confirmed

    # Availability condition - would normally check a real calendar
    elif condition.type == "availability":
      # For demo, we're just checking if the user input contains availability info
      if "available" in user_input.lower():
        is_available = "not available" not in user_input.lower()
        return (condition.value is True and is_available) or (condition.value is False and not is_available)

      # Default availability
      return condition.value is True

    # Time range condition
    elif condition.type == "time_range":
      entities = context.get("entities", {})
      if "time" in entities:
        try:
          # Parse time from entity (simplified)
          time_str = entities["time"]
          hour = int(time_str.split(":")[0])
          minute = int(time_str.split(":")[1].split()[0])
          is_pm = "PM" in time_str.upper()

          if is_pm and hour < 12:
            hour += 12
          elif not is_pm and hour == 12:
            hour = 0

          entity_time = time(hour, minute)

          # Get time range from condition
          range_start, range_end = condition.value
          start_hour, start_minute = map(int, range_start.split(":"))
          end_hour, end_minute = map(int, range_end.split(":"))

          start_time = time(start_hour, start_minute)
          end_time = time(end_hour, end_minute)

          # Check if time is within range
          is_in_range = start_time <= entity_time <= end_time
          return is_in_range if condition.operator == "in_range" else not is_in_range
        except Exception:
          return False
      return False

    # Default behavior: condition not recognized
    return False
