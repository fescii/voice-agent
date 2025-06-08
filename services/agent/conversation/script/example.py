"""
Full example of using the advanced node/edge script flow system.
"""
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from models.internal.callcontext import CallContext, CallDirection, CallStatus
from services.llm.orchestrator import LLMOrchestrator
from services.llm.prompt.manager import PromptManager
from services.llm.prompt.adapter import PromptLLMAdapter
from services.agent.core import AgentCore
from services.agent.conversation import ConversationManager, ScriptConversationFlow
from services.llm.script.agent import VoiceAgentScriptManager
from services.llm.script.schema import ScriptSchema
from services.agent.conversation.script import (
    create_appointment_script_with_edges,
    TransitionHandler,
    ScriptFlowExecutor
)
from data.db.models.agentconfig import AgentConfig


async def run_advanced_script_flow():
  """Full example of node/edge driven script flow."""
  print("Initializing script flow components...")

  # Create agent config
  agent_config = AgentConfig(
      id="advanced_agent",
      name="Advanced Script Agent",
      description="Demo of advanced script features",
      config={
          "personality": {
              "role": "scheduling assistant",
              "traits": ["helpful", "professional", "efficient"],
              "style": "conversational"
          }
      }
  )

  # Initialize LLM and agent components
  llm_orchestrator = LLMOrchestrator()
  prompt_manager = PromptManager()
  llm_adapter = PromptLLMAdapter(llm_orchestrator, prompt_manager)

  agent_core = AgentCore(agent_config, llm_orchestrator)
  conversation_manager = ConversationManager(agent_core)
  script_manager = VoiceAgentScriptManager(
      agent_core, prompt_manager, llm_adapter)
  script_flow = ScriptConversationFlow(conversation_manager, script_manager)

  # Get the advanced appointment script
  print("Creating advanced appointment script...")
  appointment_script = create_appointment_script_with_edges()

  # Load script
  success = await script_manager.load_script(appointment_script)
  if not success:
    print("Failed to load script")
    return

  # Create call context
  call_id = "full-example-123"
  call_context = CallContext(
      call_id=call_id,
      session_id="full-example-session",
      phone_number="+15551234567",
      agent_id="advanced_agent",
      direction=CallDirection.INBOUND,
      status=CallStatus.IN_PROGRESS,
      start_time=datetime.now(),
      end_time=None,
      duration=0,
      ringover_call_id="ringover-abc",
      websocket_id="ws-xyz"
  )

  # Initialize agent
  await agent_core.initialize(call_context)

  # Activate script flow
  print("Activating script flow...")
  activated = await script_flow.activate_script_flow(
      call_context, "appointment_scheduling_advanced"
  )
  if not activated:
    print("Failed to activate script flow")
    return

  # Get loaded script from manager
  script = script_manager.script_manager.get_script(
      "appointment_scheduling_advanced")
  if not script:
    print("Failed to retrieve script")
    return

  # Create transition handler
  transition_handler = TransitionHandler(script)

  # Create script executor
  executor = ScriptFlowExecutor(script_flow, transition_handler, call_id)

  # Initialize executor
  initialized = await executor.initialize()
  if not initialized:
    print("Failed to initialize executor")
    return

  print("Script flow system ready\n")

  # Run conversation with node/edge transitions
  conversation = [
      (
          "Hi, I need to schedule a doctor's appointment",
          "greeting"  # Starting state
      ),
      (
          "My name is Alex Johnson, and I need an appointment for an annual checkup on Monday at 2 PM",
          "collect_information"
      ),
      (
          "Yes, I can see that time is available",
          "check_availability"
      ),
      (
          "Let me confirm the details. You're Alex Johnson, coming in for an annual checkup on Monday at 2 PM. Is that all correct?",
          "confirm_details"
      ),
      (
          "Yes, that's all correct",
          "schedule_appointment"
      ),
      (
          "I prefer email confirmation",
          "handle_confirmation_preference"
      ),
      (
          "My email is alex.johnson@example.com",
          "closing"
      ),
      (
          "Thank you, goodbye!",
          None
      )
  ]

  # Process each turn with the executor
  for i, (user_input, expected_state) in enumerate(conversation):
    print(f"\n--- Turn {i+1} ---")
    print(f"User: {user_input}")

    # Process turn
    response, next_state = await executor.process_turn(call_context, user_input)

    # Print agent response
    if response:
      print(f"Agent: {response.text}")
    else:
      print("Agent: No response")

    # Get current state
    current_state = executor.current_state
    print(f"Current state: {current_state}")

    # Transition to next state if determined
    if next_state and next_state != current_state:
      print(f"Transitioning to: {next_state}")
      await executor.transition_if_needed(next_state)

    # If there's an expected state for the next turn, transition to it
    # This is for simulation purposes - normally the transitions would be based on the edge conditions
    if expected_state and expected_state != executor.current_state:
      print(f"Forcing transition to expected state: {expected_state}")
      await script_flow.transition_script_state(call_id, expected_state)
      executor.current_state = expected_state

  # Complete the script flow
  await executor.complete()
  print("\nScript flow execution completed")

  # Print summary
  print("\n--- Conversation Summary ---")
  print(f"Entities collected: {executor.context['entities']}")
  print(f"Intent history: {executor.context['intents']}")
  print(
      f"States traversed: {[turn['state'] for turn in executor.context['history']]}")


if __name__ == "__main__":
  asyncio.run(run_advanced_script_flow())
