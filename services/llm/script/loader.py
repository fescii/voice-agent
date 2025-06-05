"""
Loader for JSON-based prompt scripts.
"""
import json
from typing import Dict, Any, Optional, Union, TextIO
from pathlib import Path

from core.logging.setup import get_logger
from .schema import ScriptSchema
from .validation import validate_script

logger = get_logger(__name__)


class ScriptLoader:
    """Loads and validates JSON prompt scripts."""

    @staticmethod
    async def load_from_file(file_path: Union[str, Path]) -> Optional[ScriptSchema]:
        """
        Load script from a JSON file.
        
        Args:
            file_path: Path to the JSON script file
            
        Returns:
            Parsed script schema or None if invalid
        """
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            
            if not path.exists():
                logger.error(f"Script file not found: {path}")
                return None
                
            with open(path, 'r') as f:
                return await ScriptLoader.load_from_stream(f)
                
        except Exception as e:
            logger.error(f"Error loading script from file {file_path}: {e}")
            return None

    @staticmethod
    async def load_from_string(json_string: str) -> Optional[ScriptSchema]:
        """
        Load script from a JSON string.
        
        Args:
            json_string: JSON script as string
            
        Returns:
            Parsed script schema or None if invalid
        """
        try:
            script_data = json.loads(json_string)
            return await ScriptLoader.load_from_dict(script_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading script from string: {e}")
            return None

    @staticmethod
    async def load_from_stream(file_stream: TextIO) -> Optional[ScriptSchema]:
        """
        Load script from a file stream.
        
        Args:
            file_stream: File-like object containing JSON
            
        Returns:
            Parsed script schema or None if invalid
        """
        try:
            script_data = json.load(file_stream)
            return await ScriptLoader.load_from_dict(script_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in stream: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading script from stream: {e}")
            return None

    @staticmethod
    async def load_from_dict(script_data: Dict[str, Any]) -> Optional[ScriptSchema]:
        """
        Load script from a dictionary.
        
        Args:
            script_data: Dictionary containing script data
            
        Returns:
            Parsed script schema or None if invalid
        """
        try:
            # Create schema object
            schema = ScriptSchema(**script_data)
            
            # Validate script logic and structure
            validation_result = await validate_script(schema)
            if not validation_result.valid:
                logger.error(f"Script validation failed: {validation_result.errors}")
                return None
                
            logger.info(f"Successfully loaded script: {schema.name}")
            return schema
            
        except Exception as e:
            logger.error(f"Error parsing script data: {e}")
            return None
