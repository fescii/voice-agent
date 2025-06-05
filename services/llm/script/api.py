"""
API interface for script operations.
"""
from typing import Dict, Any, Optional, List
import json

from core.logging.setup import get_logger
from services.llm.script.manager import ScriptManager
from services.llm.script.examples import (
    create_basic_script,
    create_customer_service_script,
    create_sales_script
)

logger = get_logger(__name__)


class ScriptAPI:
  """API interface for script operations."""

  def __init__(self, script_manager: ScriptManager):
    """
    Initialize the script API.

    Args:
        script_manager: The script manager to use
    """
    self.script_manager = script_manager

  async def load_script_from_json(self, json_data: Dict[str, Any], make_default: bool = False) -> Dict[str, Any]:
    """
    Load a script from JSON data.

    Args:
        json_data: The script JSON data
        make_default: Whether to make this the default template

    Returns:
        Response with status and message
    """
    try:
      script = await self.script_manager.load_and_register_script(json_data, make_default)

      if not script:
        return {
            "success": False,
            "error": "Failed to load script"
        }

      return {
          "success": True,
          "message": f"Successfully loaded script: {script.name}",
          "script_name": script.name
      }

    except Exception as e:
      logger.error(f"Error loading script from JSON: {e}")
      return {
          "success": False,
          "error": str(e)
      }

  async def get_example_script(self, script_type: str) -> Dict[str, Any]:
    """
    Get an example script by type.

    Args:
        script_type: Type of example script to get

    Returns:
        Example script JSON
    """
    if script_type == "basic":
      return create_basic_script()
    elif script_type == "customer_service":
      return create_customer_service_script()
    elif script_type == "sales":
      return create_sales_script()
    else:
      return {
          "success": False,
          "error": f"Unknown script type: {script_type}",
          "available_types": ["basic", "customer_service", "sales"]
      }

  async def list_loaded_scripts(self) -> List[Dict[str, Any]]:
    """
    List all loaded scripts.

    Returns:
        List of script summaries
    """
    result = []
    # Get all script names
    script_names = list(self.script_manager.scripts.keys())

    # Get script details using the provided method
    for name in script_names:
      script = self.script_manager.get_script(name)
      if script:
        result.append({
            "name": name,
            "description": script.description,
            "version": script.version,
            "states_count": len(script.states),
            "tools_count": len(script.tools)
        })

    return result
