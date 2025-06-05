"""
Script-driven agent integration tests.
"""
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List

from models.internal.callcontext import CallContext, CallDirection, CallStatus
from services.llm.orchestrator import LLMOrchestrator
from services.llm.prompt.manager import PromptManager
from services.llm.prompt.adapter import PromptLLMAdapter
from services.llm.script.agent import VoiceAgentScriptManager
from services.agent.core import AgentCore, AgentState
from services.agent.conversation import (
    ScriptConversationFlow, ConversationFlow,
    ConversationTurn, ConversationManager
)
from data.db.models.agentconfig import AgentConfig


async def setup_test_environment():
  """Set up test environment with all required components."""
  # Create a basic agent config
  agent_config = AgentConfig(
      id="test_agent",
      name="TestAgent",
      description="Test Agent for Script Integration",
      config={
          "personality": {
              "role": "customer service representative",
              "traits": ["helpful", "professional"],
              "style": "friendly"
          },
          "temperature": 0.7
      }
  )

  # Create LLM components
  llm_orchestrator = LLMOrchestrator()
  prompt_manager = PromptManager()
  llm_adapter = PromptLLMAdapter(llm_orchestrator, prompt_manager)

  # Create agent components
  agent_core = AgentCore(agent_config, llm_orchestrator)
  conversation_manager = ConversationManager(agent_core)

  # Create script components
  script_manager = VoiceAgentScriptManager(
      agent_core, prompt_manager, llm_adapter)
  script_flow = ScriptConversationFlow(conversation_manager, script_manager)

  return {
      "agent_core": agent_core,
      "prompt_manager": prompt_manager,
      "llm_adapter": llm_adapter,
      "conversation_manager": conversation_manager,
      "script_manager": script_manager,
      "script_flow": script_flow
  }


async def load_example_script(script_manager):
  """Load an example script for testing."""
  # Example simple script
  example_script = {
      "name": "customer_greeting",
      "description": "Simple customer greeting script",
      "version": "1.0",
      "starting_state": "greeting",
      "states": [
          {
              "name": "greeting",
              "prompt": "You are a friendly customer service agent. Greet the customer warmly and ask how you can help them today.",
              "transitions": ["information_gathering"]
          },
          {
              "name": "information_gathering",
              "prompt": "You are collecting information from the customer. Ask clarifying questions about their needs. Focus on understanding their request fully.",
              "transitions": ["solution"]
          },
          {
              "name": "solution",
              "prompt": "Now that you understand the customer's request, provide a helpful solution. Be specific and address their needs directly.",
              "transitions": ["closing"]
          },
          {
              "name": "closing",
              "prompt": "Thank the customer for their time and ask if there's anything else you can help them with today.",
              "transitions": []
          }
      ]
  }

  success = await script_manager.load_script(example_script)
  return success


async def test_script_flow():
  """Test the script-based conversation flow."""
  print("Setting up test environment...")
  components = await setup_test_environment()

  script_manager = components["script_manager"]
  script_flow = components["script_flow"]

  # Load example script
  print("Loading example script...")
  success = await load_example_script(script_manager)
  if not success:
    print("Failed to load example script")
    return

  print("Successfully loaded example script")

  # Create a test call context
  call_context = CallContext(
      call_id="test-call-123",
      session_id="test-session-123",
      phone_number="+15551234567",
      agent_id="test-agent-id",
      direction=CallDirection.INBOUND,
      status=CallStatus.IN_PROGRESS,
      start_time=datetime.now(),
      end_time=None,
      duration=None,
      ringover_call_id=None,
      websocket_id=None
  )

  # Activate script flow
  print("Activating script flow...")
  success = await script_flow.activate_script_flow(
      call_context, "customer_greeting"
  )

  if not success:
    print("Failed to activate script flow")
    return

  print("Successfully activated script flow")

  # Process conversation turns
  print("\nTesting conversation flow:")

  # Turn 1: Greeting
  print("\n--- Turn 1 ---")
  response1 = await script_flow.process_script_turn(
      call_context, "Hello, I need some help."
  )
  print(f"User: Hello, I need some help.")
  print(f"Agent: {response1.text}")

  # Turn 2: Information gathering
  print("\n--- Turn 2 ---")
  await script_flow.transition_script_state("test-call-123", "information_gathering")
  response2 = await script_flow.process_script_turn(
      call_context, "I'm having trouble accessing my account."
  )
  print(f"User: I'm having trouble accessing my account.")
  print(f"Agent: {response2.text}")

  # Turn 3: Solution
  print("\n--- Turn 3 ---")
  await script_flow.transition_script_state("test-call-123", "solution")
  response3 = await script_flow.process_script_turn(
      call_context, "Yes, I've tried resetting my password but it didn't work."
  )
  print(f"User: Yes, I've tried resetting my password but it didn't work.")
  print(f"Agent: {response3.text}")

  # Turn 4: Closing
  print("\n--- Turn 4 ---")
  await script_flow.transition_script_state("test-call-123", "closing")
  response4 = await script_flow.process_script_turn(
      call_context, "That worked, thank you!"
  )
  print(f"User: That worked, thank you!")
  print(f"Agent: {response4.text}")

  # Get active script info
  script_info = script_flow.get_active_script_info("test-call-123")
  print(f"\nActive script info: {script_info}")

  # Deactivate script flow
  print("\nDeactivating script flow...")
  success = await script_flow.deactivate_script_flow("test-call-123")
  print(f"Successfully deactivated: {success}")


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  asyncio.run(test_script_flow())
