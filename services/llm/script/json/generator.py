"""
JSON script generator for creating and exporting script files.
"""
from typing import Dict, Any, Optional, List, Union
import json
import os
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.llm.script.json.converter import JSONScriptConverter

logger = get_logger(__name__)


class JSONScriptGenerator:
  """
  Generates and exports scripts as JSON files.
  """

  @staticmethod
  def export_script_to_file(
      script: ScriptSchema,
      output_directory: Union[str, Path],
      filename: Optional[str] = None
  ) -> Optional[Path]:
    """
    Export a script schema to a JSON file.

    Args:
        script: Script schema to export
        output_directory: Directory where the file will be saved
        filename: Optional filename (defaults to script.name.json)

    Returns:
        Path to the generated file or None on failure
    """
    try:
      # Ensure output directory exists
      output_dir = Path(output_directory) if isinstance(
          output_directory, str) else output_directory
      os.makedirs(output_dir, exist_ok=True)

      # Generate filename if not provided
      if not filename:
        filename = f"{script.name.lower().replace(' ', '_')}.json"

      # Make sure filename has .json extension
      if not filename.endswith('.json'):
        filename += '.json'

      # Create full path
      file_path = output_dir / filename

      # Convert to JSON and write to file
      json_content = JSONScriptConverter.script_to_json(script)
      with open(file_path, 'w') as f:
        f.write(json_content)

      logger.info(f"Exported script {script.name} to {file_path}")
      return file_path

    except Exception as e:
      logger.error(f"Failed to export script {script.name}: {e}")
      return None

  @staticmethod
  def export_dict_to_file(
      script_dict: Dict[str, Any],
      output_directory: Union[str, Path],
      filename: str
  ) -> Optional[Path]:
    """
    Export a script dictionary directly to a JSON file.

    Args:
        script_dict: Script data as dictionary
        output_directory: Directory where the file will be saved
        filename: Filename for the JSON file

    Returns:
        Path to the generated file or None on failure
    """
    try:
      # Ensure output directory exists
      output_dir = Path(output_directory) if isinstance(
          output_directory, str) else output_directory
      os.makedirs(output_dir, exist_ok=True)

      # Make sure filename has .json extension
      if not filename.endswith('.json'):
        filename += '.json'

      # Create full path
      file_path = output_dir / filename

      # Convert to JSON and write to file
      with open(file_path, 'w') as f:
        json.dump(script_dict, f, indent=2)

      logger.info(f"Exported script to {file_path}")
      return file_path

    except Exception as e:
      logger.error(f"Failed to export script: {e}")
      return None
