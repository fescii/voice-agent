"""
Main demonstration of script loading and visualization.
"""
import os
import asyncio
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.agent.conversation.script.advanced import validate_script_structure
from services.agent.conversation.script.visualize import ScriptFlowVisualizer
from services.agent.conversation.script.loader.file import load_from_path, load_all
from services.agent.conversation.script.loader.display import print_script_summary

logger = get_logger(__name__)


async def create_visualizations(
    script: ScriptSchema,
    output_dir: Union[str, Path],
    script_path: Union[str, Path]
) -> Dict[str, Path]:
  """
  Create various visualizations of a script.

  Args:
      script: The script to visualize
      output_dir: Directory to save visualizations
      script_path: Original script path for reference

  Returns:
      Dictionary mapping visualization type to file path
  """
  # Create output directory
  output_dir = Path(output_dir) if isinstance(output_dir, str) else output_dir
  os.makedirs(output_dir, exist_ok=True)

  script_name = Path(script_path).stem
  results = {}

  # Generate Mermaid flowchart
  mermaid_path = output_dir / f"{script_name}.md"
  await ScriptFlowVisualizer.generate_mermaid_flowchart(script_path, mermaid_path)
  results["mermaid"] = mermaid_path

  # Generate HTML visualization
  html_path = output_dir / f"{script_name}.html"
  await ScriptFlowVisualizer.generate_html_visualization(script_path, html_path)
  results["html"] = html_path

  return results


async def process_script(script_path: Union[str, Path]) -> Dict[str, Any]:
  """
  Process a script file with validations and visualizations.

  Args:
      script_path: Path to the script file

  Returns:
      Dictionary with processing results
  """
  results = {
      "path": str(script_path),
      "filename": Path(script_path).name,
      "valid": False,
      "errors": []
  }

  # Validate script structure
  validation = await validate_script_structure(script_path)
  results.update(validation)

  if not validation.get("valid"):
    return results

  # Load the script
  script = await load_from_path(script_path)
  if not script:
    results["errors"].append("Failed to load script")
    return results

  # Add script info
  results["name"] = script.name
  results["description"] = script.description
  results["states"] = len(script.states)
  results["edges"] = len(script.edges)

  # Print summary
  await print_script_summary(script)

  # Create visualizations
  vis_dir = Path.cwd() / "visualizations"
  vis_results = await create_visualizations(script, vis_dir, script_path)
  results["visualizations"] = {k: str(v) for k, v in vis_results.items()}

  return results


async def main() -> None:
  """Main entry point for script processing demonstration."""
  # Path to our JSON scripts
  script_dir = Path(__file__).parent.parent / "json"

  # Check if directory exists
  if not script_dir.exists():
    print(f"Script directory not found: {script_dir}")
    return

  # Find all JSON scripts
  script_files = list(script_dir.glob("*.json"))
  if not script_files:
    print("No script files found.")
    return

  # Print available scripts
  print(f"Found {len(script_files)} script files:")
  for i, script_file in enumerate(script_files):
    print(f"  {i+1}. {script_file.name}")

  # Process each script
  for script_file in script_files:
    print("\n" + "="*50)
    print(f"Processing: {script_file.name}")
    print("="*50)
    await process_script(script_file)

  print("\nAll scripts processed successfully!")


if __name__ == "__main__":
  asyncio.run(main())
