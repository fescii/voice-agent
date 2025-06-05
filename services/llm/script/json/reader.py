"""
File-based JSON script loader for extracting scripts from files.
"""
import os
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.llm.script.loader import ScriptLoader

logger = get_logger(__name__)


class JSONScriptFileReader:
  """
  Reads and loads JSON script files from a directory structure.
  """

  def __init__(self, base_directory: Union[str, Path]):
    """
    Initialize with a base directory for script files.

    Args:
        base_directory: Base directory containing JSON scripts
    """
    self.base_directory = Path(base_directory) if isinstance(
        base_directory, str) else base_directory

  async def load_all_scripts(self) -> Dict[str, ScriptSchema]:
    """
    Load all JSON script files from the base directory.

    Returns:
        Dictionary mapping script names to loaded script schemas
    """
    script_files = self._find_json_files()
    scripts = {}

    for file_path in script_files:
      try:
        script = await ScriptLoader.load_from_file(file_path)
        if script:
          scripts[script.name] = script
      except Exception as e:
        logger.error(f"Error loading script from {file_path}: {e}")

    return scripts

  async def load_script_by_name(self, script_name: str) -> Optional[ScriptSchema]:
    """
    Load a specific script by name.

    Args:
        script_name: Name of the script to load

    Returns:
        Loaded script schema or None if not found
    """
    script_files = self._find_json_files()

    for file_path in script_files:
      try:
        # Quick check if this might be the right file
        if self._file_name_matches(file_path, script_name):
          script = await ScriptLoader.load_from_file(file_path)
          if script and script.name == script_name:
            return script
      except Exception as e:
        logger.error(f"Error checking script {file_path}: {e}")

    logger.warning(f"Script not found: {script_name}")
    return None

  def _find_json_files(self) -> List[Path]:
    """
    Find all JSON files in the base directory.

    Returns:
        List of JSON file paths
    """
    json_files = []

    if not self.base_directory.exists():
      logger.warning(f"Script directory does not exist: {self.base_directory}")
      return json_files

    # Walk through all subdirectories
    for root, _, files in os.walk(self.base_directory):
      for file in files:
        if file.endswith('.json'):
          json_files.append(Path(root) / file)

    return json_files

  def _file_name_matches(self, file_path: Path, script_name: str) -> bool:
    """
    Check if a file name might match a script name.

    Args:
        file_path: Path to the file
        script_name: Name of the script

    Returns:
        Whether the file name might match the script name
    """
    # Simple heuristic: check if the script name is in the file name
    file_stem = file_path.stem.lower().replace('-', '_').replace(' ', '_')
    script_name_normalized = script_name.lower().replace('-', '_').replace(' ', '_')

    return script_name_normalized in file_stem
