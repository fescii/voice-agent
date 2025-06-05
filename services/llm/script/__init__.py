"""
Script module for JSON-based LLM prompt scripts.
"""
from .schema import (
    ScriptSchema,
    ScriptSection,
    State,
    Edge,
    ToolDefinition,
    StateType,
    EdgeCondition
)
from .loader import ScriptLoader
from .validation import validate_script, ValidationResult
from .converter import ScriptConverter
from .manager import ScriptManager
from .examples import (
    create_basic_script,
    create_customer_service_script,
    create_sales_script
)
from .api import ScriptAPI
from .agent import VoiceAgentScriptManager
from .parser import ScriptNodeEdgeParser
from .json import (
    JSONScriptFileReader,
    JSONScriptConverter,
    JSONScriptGenerator,
    generate_appointment_script_json,
    generate_customer_service_json
)

__all__ = [
    # Schema classes
    "ScriptSchema",
    "ScriptSection",
    "State",
    "Edge",
    "ToolDefinition",
    "StateType",
    "EdgeCondition",

    # Core functionality
    "ScriptLoader",
    "validate_script",
    "ValidationResult",
    "ScriptConverter",
    "ScriptManager",
    "ScriptAPI",
    "VoiceAgentScriptManager",

    # Node/Edge parsing
    "ScriptNodeEdgeParser",

    # Example scripts
    "create_basic_script",
    "create_customer_service_script",
    "create_sales_script",

    # JSON utilities
    "JSONScriptFileReader",
    "JSONScriptConverter",
    "JSONScriptGenerator",
    "generate_appointment_script_json",
    "generate_customer_service_json"
]
