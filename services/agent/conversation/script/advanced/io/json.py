"""
JSON input/output operations for scripts.
"""
from typing import Dict, Any, Optional, Union
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.llm.script.loader import ScriptLoader
from services.llm.script.json.generator import JSONScriptGenerator

logger = get_logger(__name__)


async def load_script_from_json(file_path: Union[str, Path]) -> Optional[ScriptSchema]:
  """
  Load a script from a JSON file.

  Args:
      file_path: Path to the JSON script file

  Returns:
      Loaded script schema or None if failed
  """
  return await ScriptLoader.load_from_file(file_path)


async def save_script_to_json(script: Dict[str, Any], output_path: Union[str, Path]) -> bool:
  """
  Save a script dictionary to a JSON file.

  Args:
      script: Script dictionary
      output_path: Path where to save the JSON file

  Returns:
      Whether the operation was successful
  """
  try:
    # Generate output directory if needed
    output_path = Path(output_path) if isinstance(
        output_path, str) else output_path
    output_dir = output_path.parent
    filename = output_path.name

    result = JSONScriptGenerator.export_dict_to_file(
        script, output_dir, filename)
    return result is not None
  except Exception as e:
    logger.error(f"Failed to save script to {output_path}: {e}")
    return False
