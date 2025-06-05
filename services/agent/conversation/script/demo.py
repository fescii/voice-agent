"""
Advanced example for script-driven voice agent flow with nodes and edges from JSON.
"""
import asyncio
import os
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from pathlib import Path

from models.internal.callcontext import CallContext, CallDirection, CallStatus
from services.llm.orchestrator import LLMOrchestrator
from services.llm.prompt.manager import PromptManager
from services.llm.prompt.adapter import PromptLLMAdapter
from services.agent.core import AgentCore
from services.agent.conversation import ConversationManager, ScriptConversationFlow
from services.llm.script.agent import VoiceAgentScriptManager
from services.agent.conversation.script.advanced import (
    create_appointment_script_with_edges,
    load_script_from_json,
    save_script_to_json,
    validate_script_structure
)
from services.llm.script.schema import ScriptSchema
from services.llm.script.json.example import (
    generate_appointment_script_json,
    generate_customer_service_json
)
from services.llm.script.json.reader import JSONScriptFileReader
from data.db.models.agentconfig import AgentConfig


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


async def advanced_script_flow_example():
  """Example of advanced script-driven voice agent flow with nodes and edges."""
  # Create agent config
  agent_config = AgentConfig(
      id="example_agent",
      name="Example Agent",
      description="An example voice agent",
      config={
          "personality": {
              "role": "scheduling assistant",
              "traits": ["helpful", "professional", "efficient"],
              "style": "conversational"
          }
      }
  )

  # Initialize LLM components
  print("Initializing components...")
  llm_orchestrator = LLMOrchestrator()
  prompt_manager = PromptManager()
  llm_adapter = PromptLLMAdapter(llm_orchestrator, prompt_manager)

  # Initialize agent components
  agent_core = AgentCore(agent_config, llm_orchestrator)
  script_manager = VoiceAgentScriptManager(
      agent_core, prompt_manager, llm_adapter)

  # Create conversation manager and script flow
  conversation_manager = ConversationManager(agent_core)
  script_flow = ScriptConversationFlow(conversation_manager, script_manager)

  # Get advanced script with nodes and edges
  appointment_script = create_appointment_script_with_edges()

  # Load script
  print("Loading advanced appointment script...")
  script_loaded = await script_manager.load_script(appointment_script)
  if not script_loaded:
    print("Failed to load advanced appointment script")
    return

  print("Advanced appointment script loaded successfully")

  # Create call context for testing
  call_context = CallContext(
      call_id="advanced-call-123",
      session_id="advanced-session-123",
      phone_number="+15551234567",
      agent_id="example-agent",
      direction=CallDirection.INBOUND,
      status=CallStatus.IN_PROGRESS,
      start_time=datetime.now(),
      end_time=None,
      duration=0,
      ringover_call_id="ringover-123",
      websocket_id="ws-123"
  )

  # Initialize agent
  await agent_core.initialize(call_context)

  # Create script state tracker
  tracker = ScriptStateTracker(script_flow, "advanced-call-123")

  # Activate script flow
  print("Activating script flow...")
  activated = await script_flow.activate_script_flow(
      call_context, "appointment_scheduling_advanced"
  )

  if not activated:
    print("Failed to activate script flow")
    return

  print("Script flow activated")

  # Example conversation flow
  print("\n--- Example Advanced Script-Driven Conversation ---\n")

  # Conversation turns with state transitions
  conversation_turns = [
      "Hi, I need to schedule a doctor's appointment",
      "My name is Alex Johnson, and I need an appointment for an annual checkup on Monday at 2 PM",
      "Yes, that slot is available",
      "Yes, everything looks correct",
      "I'd prefer email confirmation",
      "My email is alex.johnson@example.com",
      "Great, thank you!"
  ]

  # Process the conversation
  for i, user_input in enumerate(conversation_turns):
    print(f"\n--- Turn {i+1} ---")
    print(f"User: {user_input}")

    # Process turn
    response = await script_flow.process_script_turn(call_context, user_input)
    print(f"Agent: {response.text if response else 'No response'}")

    # Get current state
    info = await tracker.track_state()
    current_state = info.get("current_state") if info else "unknown"
    print(f"Current state: {current_state}")

    # Determine next state based on user input
    next_state = await tracker.handle_transition(user_input)
    if next_state and next_state != current_state:
      print(f"Transitioning to: {next_state}")
      await script_flow.transition_script_state("advanced-call-123", next_state)

  # Clean up
  await script_flow.deactivate_script_flow("advanced-call-123")
  print("\nScript flow deactivated")


async def demonstrate_json_scripts() -> None:
  """
  Demonstrate loading and using JSON scripts.
  """
  print("\n===== JSON SCRIPT DEMONSTRATION =====\n")

  # Create scripts directory if it doesn't exist
  script_dir = Path.cwd() / "scripts"
  os.makedirs(script_dir, exist_ok=True)

  # Generate JSON examples
  appointment_json = generate_appointment_script_json()
  customer_service_json = generate_customer_service_json()

  # Save to files
  appointment_path = script_dir / "appointment.json"
  with open(appointment_path, "w") as f:
    f.write(appointment_json)

  customer_service_path = script_dir / "customer_service.json"
  with open(customer_service_path, "w") as f:
    f.write(customer_service_json)

  print(f"Generated example scripts in {script_dir}")

  # Also save the programmatic example
  programmatic_script = create_appointment_script_with_edges()
  programmatic_path = script_dir / "appointment_programmatic.json"
  await save_script_to_json(programmatic_script, programmatic_path)

  # Validate the scripts
  for script_path in [appointment_path, customer_service_path, programmatic_path]:
    print(f"\nValidating script: {script_path.name}")
    validation = await validate_script_structure(script_path)

    if validation.get("valid"):
      script = await load_script_from_json(script_path)
      if script:
        print(f"✅ Successfully loaded and validated {script.name}")
        print(f"   Number of states: {len(script.states)}")
        print(f"   Number of edges: {len(script.edges)}")
        print(f"   Starting state: {script.starting_state}")
    else:
      print(f"❌ Validation failed:")
      for error in validation.get("errors", []):
        print(f"   - {error}")

  print("\nJSON script demonstration complete!")


async def analyze_script_flow(script_path: Union[str, Path]) -> None:
  """
  Analyze a script's flow structure.

  Args:
      script_path: Path to the script file
  """
  print(f"\n===== ANALYZING SCRIPT FLOW: {script_path} =====\n")

  script = await load_script_from_json(script_path)
  if not script:
    print("Failed to load script")
    return

  # Create a map of states by name
  states_by_name = {state.name: state for state in script.states}

  # Create a graph of state transitions
  graph = {}
  for state in script.states:
    graph[state.name] = []

  for edge in script.edges:
    if edge.from_state not in graph:
      graph[edge.from_state] = []
    graph[edge.from_state].append(edge.to_state)

  # Print flow stats
  print(f"Script: {script.name}")
  print(f"Total states: {len(script.states)}")
  print(f"Total edges: {len(script.edges)}")
  print(f"Starting state: {script.starting_state}")

  # Identify terminal states
  terminal_states = [
      s.name for s in script.states if s.type.value == "terminal"]
  print(
      f"Terminal states: {', '.join(terminal_states) if terminal_states else 'None'}")

  # Identify decision points
  decision_states = [
      s.name for s in script.states if s.type.value == "decision"]
  print(
      f"Decision points: {', '.join(decision_states) if decision_states else 'None'}")

  # Find longest path if we have a starting state
  starting_state = script.starting_state or (
      script.states[0].name if script.states else "")
  if starting_state:
    longest_path = find_longest_path(graph, starting_state)
    print(f"Longest possible path: {' -> '.join(longest_path)}")
    print(f"Max path length: {len(longest_path) - 1} transitions")
  else:
    print("No starting state defined, cannot analyze paths")

  print("\nFlow analysis complete!")


def find_longest_path(graph: Dict[str, List[str]], start: str) -> List[str]:
  """
  Find the longest possible path in a directed graph.

  Args:
      graph: Adjacency list representation of the graph
      start: Starting node

  Returns:
      List of nodes in the longest path
  """
  # Use dynamic programming to find longest path
  memo = {}

  def dfs(node):
    if node in memo:
      return memo[node]

    if not graph.get(node, []):
      return [node]

    max_path = [node]

    for neighbor in graph.get(node, []):
      path = dfs(neighbor)
      if len(path) + 1 > len(max_path):
        max_path = [node] + path

    memo[node] = max_path
    return max_path

  return dfs(start)


if __name__ == "__main__":
  asyncio.run(advanced_script_flow_example())
  asyncio.run(demonstrate_json_scripts())

  # Optionally analyze a specific script file
  script_path = Path.cwd() / "scripts" / "customer_service.json"
  if script_path.exists():
    asyncio.run(analyze_script_flow(script_path))
