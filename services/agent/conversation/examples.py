"""
Usage examples for script-driven voice agent flow.
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime

from models.internal.callcontext import CallContext, CallDirection, CallStatus
from services.llm.orchestrator import LLMOrchestrator
from services.llm.prompt.manager import PromptManager
from services.llm.prompt.adapter import PromptLLMAdapter
from services.agent.core import AgentCore
from services.agent.conversation import ConversationManager, ScriptConversationFlow
from services.llm.script.agent import VoiceAgentScriptManager
from data.db.models.agentconfig import AgentConfig


async def example_script_flow():
  """Example of script-driven voice agent flow."""
  # Create agent config
  agent_config = AgentConfig(
      id="example_agent",
      name="Example Agent",
      description="An example voice agent",
      config={
          "personality": {
              "role": "customer service representative",
              "traits": ["helpful", "professional"],
              "style": "conversational"
          }
      }
  )

  # Initialize LLM components
  llm_orchestrator = LLMOrchestrator()
  prompt_manager = PromptManager()
  llm_adapter = PromptLLMAdapter(llm_orchestrator, prompt_manager)

  # Initialize agent components
  agent_core = AgentCore(agent_config, llm_orchestrator)
  script_manager = VoiceAgentScriptManager(
      agent_core, prompt_manager, llm_adapter)

  # Create a simple script JSON
  appointment_script = {
      "name": "appointment_scheduling",
      "description": "Script for scheduling appointments",
      "version": "1.0",
      "starting_state": "greeting",
      "states": [
          {
              "name": "greeting",
              "prompt": "You are a friendly scheduling assistant. Greet the caller and ask how you can help them today. Remember to introduce yourself as {agent_name}.",
              "transitions": ["collect_information"]
          },
          {
              "name": "collect_information",
              "prompt": "You are collecting appointment information. Ask for the caller's name, preferred date and time for the appointment, and reason for the appointment. If they've already provided some information, only ask for what's missing.",
              "transitions": ["confirm_details"]
          },
          {
              "name": "confirm_details",
              "prompt": "Confirm the appointment details with the caller. Read back their name, the date and time, and the reason for the appointment. Ask if everything is correct.",
              "transitions": ["schedule_appointment", "collect_information"]
          },
          {
              "name": "schedule_appointment",
              "prompt": "Thank the caller for confirming the details. Let them know that you're scheduling their appointment now. Tell them they will receive a confirmation via email or text message. Ask if there's anything else they need help with.",
              "transitions": ["closing"]
          },
          {
              "name": "closing",
              "prompt": "Thank the caller for contacting you. Wish them a good day and end the call professionally.",
              "transitions": []
          }
      ]
  }

  # Load script
  script_loaded = await script_manager.load_script(appointment_script)
  if not script_loaded:
    print("Failed to load appointment script")
    return

  print("Appointment script loaded successfully")

  # Create call context for testing
  call_context = CallContext(
      call_id="example-call-123",
      session_id="example-session-123",
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

  # Create a simplified conversation manager for testing
  conversation_manager = ConversationManager(agent_core)

  # Create script flow manager
  script_flow = ScriptConversationFlow(conversation_manager, script_manager)

  # Activate script flow
  activated = await script_flow.activate_script_flow(
      call_context, "appointment_scheduling"
  )

  if not activated:
    print("Failed to activate script flow")
    return

  print("Script flow activated")

  # Example conversation flow
  print("\n--- Example Script-Driven Conversation ---\n")

  # Turn 1: Greeting
  user_input_1 = "Hi, I need to schedule an appointment"
  print(f"User: {user_input_1}")

  response_1 = await script_flow.process_script_turn(call_context, user_input_1)
  print(f"Agent: {response_1.text if response_1 else 'No response'}\n")

  # Turn 2: Collect information
  await script_flow.transition_script_state("example-call-123", "collect_information")
  user_input_2 = "My name is Alex Johnson, I'd like to schedule for next Tuesday at 2 PM for a dental cleaning"
  print(f"User: {user_input_2}")

  response_2 = await script_flow.process_script_turn(call_context, user_input_2)
  print(f"Agent: {response_2.text if response_2 else 'No response'}\n")

  # Turn 3: Confirm details
  await script_flow.transition_script_state("example-call-123", "confirm_details")
  user_input_3 = "Yes, that's all correct"
  print(f"User: {user_input_3}")

  response_3 = await script_flow.process_script_turn(call_context, user_input_3)
  print(f"Agent: {response_3.text if response_3 else 'No response'}\n")

  # Turn 4: Schedule appointment
  await script_flow.transition_script_state("example-call-123", "schedule_appointment")
  user_input_4 = "No, that's all I needed. Thanks!"
  print(f"User: {user_input_4}")

  response_4 = await script_flow.process_script_turn(call_context, user_input_4)
  print(f"Agent: {response_4.text if response_4 else 'No response'}\n")

  # Turn 5: Closing
  await script_flow.transition_script_state("example-call-123", "closing")
  user_input_5 = "Goodbye!"
  print(f"User: {user_input_5}")

  response_5 = await script_flow.process_script_turn(call_context, user_input_5)
  print(f"Agent: {response_5.text if response_5 else 'No response'}\n")

  # Clean up
  await script_flow.deactivate_script_flow("example-call-123")
  print("Script flow deactivated")


if __name__ == "__main__":
  asyncio.run(example_script_flow())
