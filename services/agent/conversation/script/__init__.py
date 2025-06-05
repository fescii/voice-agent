"""
Script example templates and utilities for conversation flows with JSON support.
"""
from .advanced import (
    create_appointment_script_with_edges,
    load_script_from_json,
    save_script_to_json,
    validate_script_structure
)
from .handler import TransitionHandler
from .executor import ScriptFlowExecutor
from .visualize import ScriptFlowVisualizer
from .loader import (
    load_from_path,
    load_all,
    find_by_name,
    display_script_info,
    print_script_summary,
    process_script,
    create_visualizations
)

__all__ = [
    # Script creation and manipulation
    "create_appointment_script_with_edges",
    "load_script_from_json",
    "save_script_to_json",
    "validate_script_structure",

    # Flow control
    "TransitionHandler",
    "ScriptFlowExecutor",

    # Visualization
    "ScriptFlowVisualizer",

    # Script loading and display
    "load_from_path",
    "load_all",
    "find_by_name",
    "display_script_info",
    "print_script_summary",
    "process_script",
    "create_visualizations"
]
