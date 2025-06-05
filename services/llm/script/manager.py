"""
Manager for handling script operations.
"""
from typing import Dict, Optional, List, Union
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.prompt.manager import PromptManager
from services.llm.script.schema import ScriptSchema
from services.llm.script.loader import ScriptLoader
from services.llm.script.converter import ScriptConverter

logger = get_logger(__name__)


class ScriptManager:
  """Manages the loading and registration of scripts."""

  def __init__(self, prompt_manager: PromptManager):
    """
    Initialize the script manager.

    Args:
        prompt_manager: The prompt manager to register scripts with
    """
    self.prompt_manager = prompt_manager
    self.scripts: Dict[str, ScriptSchema] = {}

  async def load_and_register_script(
      self,
      source: Union[str, Path, Dict],
      make_default: bool = False
  ) -> Optional[ScriptSchema]:
    """
    Load and register a script from various sources.

    Args:
        source: Source of the script (file path, JSON string, or dict)
        make_default: Whether to make this the default template

    Returns:
        The loaded script if successful, None otherwise
    """
    script = None

    # Load script based on source type
    if isinstance(source, dict):
      script = await ScriptLoader.load_from_dict(source)
    elif isinstance(source, (str, Path)) and Path(source).exists():
      script = await ScriptLoader.load_from_file(source)
    elif isinstance(source, str):
      # Try to parse as JSON string
      script = await ScriptLoader.load_from_string(source)

    if not script:
      logger.error("Failed to load script from source")
      return None

    # Register script
    success = await ScriptConverter.register_script(
        script=script,
        prompt_manager=self.prompt_manager,
        make_default=make_default
    )

    if not success:
      return None

    # Store script reference
    self.scripts[script.name] = script
    return script

  async def load_scripts_from_directory(self, directory_path: Union[str, Path]) -> List[ScriptSchema]:
    """
    Load all scripts from a directory.

    Args:
        directory_path: Directory containing JSON script files

    Returns:
        List of successfully loaded scripts
    """
    path = Path(directory_path) if isinstance(
        directory_path, str) else directory_path

    if not path.exists() or not path.is_dir():
      logger.error(f"Directory not found: {path}")
      return []

    loaded_scripts = []

    # Find all .json files
    for file_path in path.glob("*.json"):
      script = await self.load_and_register_script(file_path)
      if script:
        loaded_scripts.append(script)

    logger.info(f"Loaded {len(loaded_scripts)} scripts from directory {path}")
    return loaded_scripts

  def get_script(self, script_name: str) -> Optional[ScriptSchema]:
    """
    Get a loaded script by name.

    Args:
        script_name: Name of the script

    Returns:
        The script if found, None otherwise
    """
    return self.scripts.get(script_name)
