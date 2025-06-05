"""
Main example demonstrating complete call flow with JSON scripts.
"""
import asyncio
import os
from pathlib import Path

from services.agent.conversation.script.loader import (
    load_from_path,
    print_script_summary,
    create_visualizations
)
from services.agent.conversation.script.advanced import validate_script_structure


async def demonstrate_script_flow() -> None:
  """Demonstrate the node/edge-based script flow."""
  print("\n===== CALL SCRIPT FLOW DEMONSTRATION =====\n")

  # Use the insurance script
  script_path = Path(__file__).parent / "json" / "insurance.json"

  # Make sure the file exists
  if not script_path.exists():
    print(f"Script file not found: {script_path}")
    return

  # Validate the script
  validation = await validate_script_structure(script_path)
  if not validation.get("valid"):
    print("Script validation failed:")
    for error in validation.get("errors", []):
      print(f"  - {error}")
    return

  # Load the script
  script = await load_from_path(script_path)
  if not script:
    print("Failed to load script")
    return

  # Print script summary
  print(f"\nLoaded script: {script.name}")
  await print_script_summary(script)

  # Generate visualizations
  vis_dir = Path.cwd() / "visualizations"
  os.makedirs(vis_dir, exist_ok=True)
  vis_files = await create_visualizations(script, vis_dir, script_path)

  print("\nCreated visualizations:")
  for format_name, file_path in vis_files.items():
    print(f"  - {format_name}: {file_path}")

  # Sample conversation flow
  print("\n===== SAMPLE CONVERSATION FLOW =====\n")

  # Simulate a simple conversation path through the script
  current_state = script.starting_state
  visited_states = set()
  path = []

  while current_state and current_state not in visited_states:
    # Get the current state
    state_obj = next(
        (s for s in script.states if s.name == current_state), None)
    if not state_obj:
      print(f"Error: State '{current_state}' not found in script")
      break

    # Print state information
    print(f"STATE: {current_state} ({state_obj.type.value})")
    print(f"PROMPT: {state_obj.prompt[:100]}...")

    # Record this state
    path.append(current_state)
    visited_states.add(current_state)

    # Find outgoing edges from this state
    next_edges = [e for e in script.edges if e.from_state == current_state]

    if not next_edges:
      print("No outgoing edges, conversation ends\n")
      break

    # Take the first edge (simplified)
    next_edge = next_edges[0]

    # Show transition
    condition = f" [Condition: {next_edge.condition.type}={next_edge.condition.value}]" if next_edge.condition else ""
    print(f"→ {next_edge.to_state}{condition}")

    # Move to next state
    current_state = next_edge.to_state
    print()

  # Print the full path
  print("\nFull conversation path:")
  print(" → ".join(path))

  print("\nDemo complete!")


if __name__ == "__main__":
  asyncio.run(demonstrate_script_flow())
