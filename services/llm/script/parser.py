"""
JSON script parser specializing in nodes and edges.
"""
from typing import Dict, Any, Optional, List, Union, Tuple
import json

from core.logging.setup import get_logger
from .schema import ScriptSchema, State, Edge, EdgeCondition, StateType

logger = get_logger(__name__)


class ScriptNodeEdgeParser:
  """
  Parser for JSON-based script nodes (states) and edges (transitions).

  This specializes in handling the graph structure of conversation flows
  defined through nodes and edges in JSON format.
  """

  @staticmethod
  def parse_nodes_from_json(nodes_data: List[Dict[str, Any]]) -> List[State]:
    """
    Parse node definitions from JSON data.

    Args:
        nodes_data: List of node data from JSON

    Returns:
        List of State objects
    """
    states = []

    for node_data in nodes_data:
      try:
        # Handle string-based state types
        state_type = node_data.get("type", "")
        if isinstance(state_type, str):
          try:
            state_type = StateType(state_type.lower())
          except ValueError:
            state_type = StateType.INFORMATION  # Default

        # Create state from node data
        state = State(
            name=node_data["name"],
            type=state_type,
            prompt=node_data["prompt"],
            tools=node_data.get("tools", []),
            description=node_data.get("description"),
            metadata=node_data.get("metadata", {})
        )
        states.append(state)
      except Exception as e:
        logger.error(
            f"Error parsing node {node_data.get('name', 'unknown')}: {e}")
        # Continue processing other nodes

    return states

  @staticmethod
  def parse_edges_from_json(edges_data: List[Dict[str, Any]]) -> List[Edge]:
    """
    Parse edge definitions from JSON data.

    Args:
        edges_data: List of edge data from JSON

    Returns:
        List of Edge objects
    """
    edges = []

    for edge_data in edges_data:
      try:
        # Parse condition if present
        condition = None
        if "condition" in edge_data:
          condition_data = edge_data["condition"]
          condition = EdgeCondition(
              type=condition_data["type"],
              value=condition_data["value"],
              operator=condition_data.get("operator", "equals")
          )

        # Create edge
        edge = Edge(
            from_state=edge_data["from_state"],
            to_state=edge_data["to_state"],
            condition=condition,
            description=edge_data.get("description")
        )
        edges.append(edge)
      except Exception as e:
        logger.error(
            f"Error parsing edge from {edge_data.get('from_state', 'unknown')} to {edge_data.get('to_state', 'unknown')}: {e}")
        # Continue processing other edges

    return edges

  @staticmethod
  def is_valid_graph_structure(states: List[State], edges: List[Edge], starting_state: Optional[str] = None) -> Tuple[bool, str]:
    """
    Validate the graph structure defined by states and edges.

    Args:
        states: List of states
        edges: List of edges
        starting_state: Optional starting state name

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check if states exist
    if not states:
      return False, "No states defined in script"

    # Create a map of state names for quick lookup
    state_names = {state.name for state in states}

    # Check if starting state exists
    if starting_state and starting_state not in state_names:
      return False, f"Starting state '{starting_state}' not found in defined states"

    # Verify all edge references exist
    for edge in edges:
      if edge.from_state not in state_names:
        return False, f"Edge references non-existent from_state '{edge.from_state}'"

      if edge.to_state not in state_names:
        return False, f"Edge references non-existent to_state '{edge.to_state}'"

    # Check for isolated states (no incoming or outgoing edges)
    states_with_edges = set()
    for edge in edges:
      states_with_edges.add(edge.from_state)
      states_with_edges.add(edge.to_state)

    isolated_states = state_names - states_with_edges
    if isolated_states and (not starting_state or starting_state not in isolated_states):
      logger.warning(
          f"Script contains isolated states: {', '.join(isolated_states)}")

    return True, ""

  @staticmethod
  def normalize_script_format(script_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize different JSON formats for script data.

    This handles various naming conventions people might use in JSON:
    - "nodes" vs "states"
    - "transitions" vs "edges"

    Args:
        script_data: Raw script data dictionary

    Returns:
        Normalized script data
    """
    normalized = script_data.copy()

    # Handle nodes vs states
    if "nodes" in normalized and "states" not in normalized:
      normalized["states"] = normalized.pop("nodes")

    # Handle transitions vs edges
    if "transitions" in normalized and "edges" not in normalized:
      normalized["edges"] = normalized.pop("transitions")

    # Normalize starting_state vs initial_state vs start
    if "initial_state" in normalized and "starting_state" not in normalized:
      normalized["starting_state"] = normalized.pop("initial_state")
    elif "start" in normalized and "starting_state" not in normalized:
      normalized["starting_state"] = normalized.pop("start")

    return normalized
