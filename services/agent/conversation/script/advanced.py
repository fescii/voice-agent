"""
Advanced script examples - thin wrapper for backward compatibility.
"""
from .advanced import (
    load_script_from_json,
    save_script_to_json,
    create_appointment_script_with_edges,
    validate_script_structure
)

__all__ = [
    'load_script_from_json',
    'save_script_to_json',
    'create_appointment_script_with_edges',
    'validate_script_structure'
]
