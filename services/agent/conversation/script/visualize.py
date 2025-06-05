"""
Script flow visualizer to generate visual representations of script flows.
"""
from typing import Dict, Any, Optional, List, Union
import json
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.llm.script.loader import ScriptLoader
from services.llm.script.json.converter import JSONScriptConverter

logger = get_logger(__name__)


class ScriptFlowVisualizer:
  """
  Creates visual representations of script flows.
  """

  @staticmethod
  async def generate_mermaid_flowchart(script_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> str:
    """
    Generate a Mermaid flowchart representation of a script.

    Args:
        script_path: Path to the script file
        output_path: Optional path to save the flowchart

    Returns:
        Mermaid flowchart string
    """
    # Load the script
    script = await ScriptLoader.load_from_file(script_path)
    if not script:
      logger.error(f"Failed to load script from {script_path}")
      return ""

    # Generate flowchart
    flowchart = JSONScriptConverter.script_to_flowchart_mermaid(script)

    # Save to file if requested
    if output_path:
      try:
        output_path = Path(output_path) if isinstance(
            output_path, str) else output_path
        with open(output_path, 'w') as f:
          f.write(flowchart)
        logger.info(f"Saved flowchart to {output_path}")
      except Exception as e:
        logger.error(f"Failed to save flowchart: {e}")

    return flowchart

  @staticmethod
  async def generate_graphviz_dot(script_path: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> str:
    """
    Generate a GraphViz DOT representation of a script.

    Args:
        script_path: Path to the script file
        output_path: Optional path to save the DOT file

    Returns:
        GraphViz DOT string
    """
    # Load the script
    script = await ScriptLoader.load_from_file(script_path)
    if not script:
      logger.error(f"Failed to load script from {script_path}")
      return ""

    # Generate DOT
    dot = JSONScriptConverter.script_to_graphviz(script)

    # Save to file if requested
    if output_path:
      try:
        output_path = Path(output_path) if isinstance(
            output_path, str) else output_path
        with open(output_path, 'w') as f:
          f.write(dot)
        logger.info(f"Saved DOT file to {output_path}")
      except Exception as e:
        logger.error(f"Failed to save DOT file: {e}")

    return dot

  @staticmethod
  def generate_ascii_flowchart(script: ScriptSchema) -> str:
    """
    Generate a simple ASCII flowchart of a script.

    Args:
        script: Script schema

    Returns:
        ASCII flowchart string
    """
    if not script or not script.states:
      return "Empty script"

    # Create a map of states and their outgoing edges
    outgoing_edges = {}
    for edge in script.edges:
      if edge.from_state not in outgoing_edges:
        outgoing_edges[edge.from_state] = []
      outgoing_edges[edge.from_state].append((edge.to_state, edge.description))

    # Start with the initial state
    result = []
    visited = set()

    def build_ascii(state_name, depth=0, prefix=""):
      if state_name in visited:
        return

      visited.add(state_name)

      # Add this state to the result
      indent = "  " * depth
      result.append(f"{indent}{prefix}[{state_name}]")

      # Process outgoing edges
      if state_name in outgoing_edges:
        edges = outgoing_edges[state_name]
        for i, (target, desc) in enumerate(edges):
          is_last = (i == len(edges) - 1)
          if is_last:
            result.append(f"{indent}  └─ {desc or ''} ─→")
            build_ascii(target, depth + 1, "")
          else:
            result.append(f"{indent}  ├─ {desc or ''} ─→")
            build_ascii(target, depth + 1, "")

    # Start with the starting state
    starting_state = script.starting_state or (
        script.states[0].name if script.states else "")
    if starting_state:
      build_ascii(starting_state)

    return "\n".join(result)

  @staticmethod
  async def generate_html_visualization(script_path: Union[str, Path], output_path: Union[str, Path]) -> bool:
    """
    Generate an HTML visualization of a script.

    Args:
        script_path: Path to the script file
        output_path: Path to save the HTML file

    Returns:
        Whether generation was successful
    """
    # Load the script
    script = await ScriptLoader.load_from_file(script_path)
    if not script:
      logger.error(f"Failed to load script from {script_path}")
      return False

    # Generate Mermaid flowchart
    mermaid_chart = JSONScriptConverter.script_to_flowchart_mermaid(script)

    # Create HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{script.name} - Script Flow Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2 {{
            color: #2c3e50;
        }}
        .mermaid {{
            margin: 20px 0;
            overflow: auto;
        }}
        .script-info {{
            background: #f8f9fa;
            border-left: 5px solid #4caf50;
            padding: 15px;
            margin-bottom: 20px;
        }}
        .states, .edges {{
            margin-top: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
    </style>
</head>
<body>
    <h1>{script.name} - Script Flow Visualization</h1>
    
    <div class="script-info">
        <h2>Script Information</h2>
        <p><strong>Description:</strong> {script.description or "No description provided"}</p>
        <p><strong>Version:</strong> {script.version}</p>
        <p><strong>Starting State:</strong> {script.starting_state}</p>
    </div>
    
    <h2>Flow Diagram</h2>
    <div class="mermaid">
{mermaid_chart}
    </div>
    
    <div class="states">
        <h2>States ({len(script.states)})</h2>
        <table>
            <tr>
                <th>Name</th>
                <th>Type</th>
                <th>Description</th>
            </tr>
            {"".join([f"<tr><td>{state.name}</td><td>{state.type.value}</td><td>{state.description or ''}</td></tr>" for state in script.states])}
        </table>
    </div>
    
    <div class="edges">
        <h2>Transitions ({len(script.edges)})</h2>
        <table>
            <tr>
                <th>From</th>
                <th>To</th>
                <th>Description</th>
                <th>Condition</th>
            </tr>
            {"".join([f"<tr><td>{edge.from_state}</td><td>{edge.to_state}</td><td>{edge.description or ''}</td><td>{edge.condition.type + ': ' + str(edge.condition.value) if edge.condition else ''}</td></tr>" for edge in script.edges])}
        </table>
    </div>
    
    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>
"""

    # Save to file
    try:
      output_path = Path(output_path) if isinstance(
          output_path, str) else output_path
      with open(output_path, 'w') as f:
        f.write(html_content)
      logger.info(f"Saved HTML visualization to {output_path}")
      return True
    except Exception as e:
      logger.error(f"Failed to save HTML visualization: {e}")
      return False
