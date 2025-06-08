"""
Advanced script flow example demonstration.
"""

import asyncio
from datetime import datetime
from typing import List

from models.internal.callcontext import CallContext, CallDirection, CallStatus
from services.llm.orchestrator import LLMOrchestrator
from services.llm.prompt.manager import PromptManager
from services.llm.prompt.adapter import PromptLLMAdapter
from services.agent.core import AgentCore
from services.agent.conversation import ConversationManager, ScriptConversationFlow
from services.llm.script.agent import VoiceAgentScriptManager
from services.agent.conversation.script.advanced import create_appointment_script_with_edges
from data.db.models.agentconfig import AgentConfig
from ..tracking.state import ScriptStateTracker


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
