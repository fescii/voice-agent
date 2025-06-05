"""
JSON script converter to transform between different script formats.
"""
from typing import Dict, Any, Optional, List, Union
import json

from services.llm.script.schema import ScriptSchema, StateType, Edge, State, EdgeCondition


class JSONScriptConverter:
  """
  Converts between different script formats and representations.
  """

  @staticmethod
  def script_to_json(script: ScriptSchema) -> str:
    """
    Convert a script schema to a JSON string.

    Args:
        script: Script schema to convert

    Returns:
        JSON string representation
    """
    # Convert to dict, then to JSON
    script_dict = script.dict()

    # Special handling for enums in JSON
    states = []
    for state in script_dict.get("states", []):
      if "type" in state and isinstance(state["type"], StateType):
        state["type"] = state["type"].value
      states.append(state)

    script_dict["states"] = states

    return json.dumps(script_dict, indent=2)

  @staticmethod
  def script_to_flowchart_mermaid(script: ScriptSchema) -> str:
    """
    Convert a script schema to a Mermaid flowchart string.

    Args:
        script: Script schema to convert

    Returns:
        Mermaid flowchart string
    """
    lines = ["flowchart TD"]

    # Add nodes (states)
    for state in script.states:
      shape = JSONScriptConverter._get_state_shape(state.type)
      lines.append(f"    {state.name}{shape}\"{state.name}\"")

    # Add edges
    for edge in script.edges:
      label = f"|{edge.description}|" if edge.description else ""
      lines.append(f"    {edge.from_state} -->|{label}| {edge.to_state}")

    return "\n".join(lines)

  @staticmethod
  def _get_state_shape(state_type: StateType) -> str:
    """Get Mermaid shape for state type."""
    if state_type == StateType.INITIAL:
      return "([]) "  # Stadium shape
    elif state_type == StateType.TERMINAL:
      return "[/] "  # Trapezoid
    elif state_type == StateType.DECISION:
      return "{{}} "  # Hexagon
    elif state_type == StateType.PROCESSING:
      return "[() ] "  # Subroutine
    else:
      return "[] "  # Rectangle

  @staticmethod
  def script_to_graphviz(script: ScriptSchema) -> str:
    """
    Convert a script schema to a GraphViz DOT string.

    Args:
        script: Script schema to convert

    Returns:
        GraphViz DOT string
    """
    lines = ["digraph CallFlow {", "    rankdir=TB;", "    node [shape=box];"]

    # Add nodes (states)
    for state in script.states:
      shape = JSONScriptConverter._get_state_shape_graphviz(state.type)
      lines.append(
          f'    {state.name} [shape="{shape}", label="{state.name}"];')

    # Add edges
    for edge in script.edges:
      label = f'label="{edge.description}"' if edge.description else ""
      lines.append(f"    {edge.from_state} -> {edge.to_state} [{label}];")

    lines.append("}")
    return "\n".join(lines)

  @staticmethod
  def _get_state_shape_graphviz(state_type: StateType) -> str:
    """Get GraphViz shape for state type."""
    if state_type == StateType.INITIAL:
      return "oval"
    elif state_type == StateType.TERMINAL:
      return "doublecircle"
    elif state_type == StateType.DECISION:
      return "diamond"
    elif state_type == StateType.PROCESSING:
      return "box3d"
    else:
      return "box"
