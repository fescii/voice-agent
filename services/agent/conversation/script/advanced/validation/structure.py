"""
Script validation functionality.
"""
from typing import Dict, Any, Union, Set
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.llm.script.loader import ScriptLoader
from services.llm.script.parser import ScriptNodeEdgeParser

logger = get_logger(__name__)


async def validate_script_structure(script_data: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
  """
  Validate a script's structure and logical flow.

  Args:
      script_data: Either a script dictionary, a JSON string, or a path to a JSON file

  Returns:
      Dictionary with validation results
  """
  try:
    # Handle different input types
    if isinstance(script_data, (str, Path)) and not isinstance(script_data, dict):
      # Check if it's a file path
      path = Path(script_data)
      if path.exists() and path.is_file():
        script = await ScriptLoader.load_from_file(path)
      else:
        # Try parsing as JSON string
        try:
          script = await ScriptLoader.load_from_string(str(script_data))
        except:
          return {
              "valid": False,
              "errors": ["Input is neither a valid file path nor a valid JSON string"]
          }
    else:
      # Assume it's a dictionary
      script = await ScriptLoader.load_from_dict(script_data)

    if not script:
      return {
          "valid": False,
          "errors": ["Failed to parse script"]
      }

    # Check graph structure
    is_valid, error_message = ScriptNodeEdgeParser.is_valid_graph_structure(
        script.states, script.edges, script.starting_state
    )

    if not is_valid:
      return {
          "valid": False,
          "errors": [error_message]
      }

    # Verify all states referenced in edges exist
    state_names = {state.name for state in script.states}
    invalid_edges = []

    for edge in script.edges:
      if edge.from_state not in state_names:
        invalid_edges.append(
            f"Edge references non-existent from_state: {edge.from_state}")
      if edge.to_state not in state_names:
        invalid_edges.append(
            f"Edge references non-existent to_state: {edge.to_state}")

    if invalid_edges:
      return {
          "valid": False,
          "errors": invalid_edges
      }

    # Check for reachability from starting state
    if not script.starting_state:
      return {
          "valid": False,
          "errors": ["No starting state defined"]
      }

    reachable_states = _find_reachable_states(
        script.starting_state, script.edges)
    unreachable_states = state_names - reachable_states

    if unreachable_states:
      return {
          "valid": False,
          "warnings": [f"Unreachable states: {', '.join(unreachable_states)}"]
      }

    return {
        "valid": True,
        "script_name": script.name,
        "state_count": len(script.states),
        "edge_count": len(script.edges)
    }

  except Exception as e:
    return {
        "valid": False,
        "errors": [f"Validation error: {str(e)}"]
    }


def _find_reachable_states(starting_state: str, edges: list) -> Set[str]:
  """
  Find all states reachable from the starting state.

  Args:
      starting_state: The starting state name
      edges: List of edges in the script

  Returns:
      Set of reachable state names
  """
  reachable_states = set()
  states_to_check = [starting_state]

  while states_to_check:
    current_state = states_to_check.pop()
    if current_state in reachable_states:
      continue

    reachable_states.add(current_state)

    # Find all states reachable from current state
    for edge in edges:
      if edge.from_state == current_state and edge.to_state not in reachable_states:
        states_to_check.append(edge.to_state)

  return reachable_states
