"""
Displaying script information in human-readable format.
"""
from typing import Dict, Any, Optional, Union
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.agent.conversation.script.visualize import ScriptFlowVisualizer
from services.agent.conversation.script.advanced import validate_script_structure

logger = get_logger(__name__)


async def display_script_info(script: ScriptSchema) -> Dict[str, Any]:
  """
  Format script information as a dictionary.

  Args:
      script: Script schema to display

  Returns:
      Dictionary with script information
  """
  # Basic script info
  info = {
      "name": script.name,
      "description": script.description,
      "version": script.version,
      "starting_state": script.starting_state,
      "state_count": len(script.states),
      "edge_count": len(script.edges),
      "state_types": {}
  }

  # Count state types
  for state in script.states:
    state_type = state.type.value
    if state_type not in info["state_types"]:
      info["state_types"][state_type] = 0
    info["state_types"][state_type] += 1

  # Extract terminals and decision points
  info["terminal_states"] = [
      s.name for s in script.states if s.type.value == "terminal"]
  info["decision_states"] = [
      s.name for s in script.states if s.type.value == "decision"]

  return info


async def print_script_summary(script: ScriptSchema) -> None:
  """
  Print a summary of the script to the console.

  Args:
      script: Script to summarize
  """
  info = await display_script_info(script)

  print(f"Script: {info['name']}")
  print(f"  Description: {info['description']}")
  print(f"  Version: {info['version']}")
  print(f"  States: {info['state_count']}")
  print(f"  Edges: {info['edge_count']}")
  print(f"  Starting state: {info['starting_state']}")

  print("\nState types:")
  for state_type, count in info["state_types"].items():
    print(f"  - {state_type}: {count}")

  print(
      f"\nTerminal states: {', '.join(info['terminal_states']) if info['terminal_states'] else 'None'}")
  print(
      f"Decision points: {', '.join(info['decision_states']) if info['decision_states'] else 'None'}")

  # Print ASCII flowchart
  print("\nASCII Flowchart Preview:")
  ascii_chart = ScriptFlowVisualizer.generate_ascii_flowchart(script)
  print(ascii_chart)
