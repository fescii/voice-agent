"""
JSON script file operations.
"""
import os
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import ScriptSchema
from services.agent.conversation.script.advanced import load_script_from_json
from services.llm.script.json.reader import JSONScriptFileReader

logger = get_logger(__name__)


async def load_from_path(script_path: Union[str, Path]) -> Optional[ScriptSchema]:
  """
  Load a JSON script from a file path.

  Args:
      script_path: Path to the JSON script file

  Returns:
      Loaded script or None if failed
  """
  return await load_script_from_json(script_path)


async def load_all(directory: Union[str, Path]) -> Dict[str, ScriptSchema]:
  """
  Load all JSON scripts from a directory.

  Args:
      directory: Directory containing JSON script files

  Returns:
      Dictionary mapping script names to loaded script schemas
  """
  reader = JSONScriptFileReader(directory)
  return await reader.load_all_scripts()


async def find_by_name(directory: Union[str, Path], script_name: str) -> Optional[ScriptSchema]:
  """
  Find and load a script by name from a directory.

  Args:
      directory: Directory to search in
      script_name: Name of the script to find

  Returns:
      Loaded script or None if not found
  """
  reader = JSONScriptFileReader(directory)
  return await reader.load_script_by_name(script_name)
