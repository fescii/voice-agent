"""
Validation for JSON-based prompt scripts.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from core.logging.setup import get_logger
from .schema import ScriptSchema, State, Edge

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """Result of script validation."""
    valid: bool
    errors: Optional[List[str]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


async def validate_script(script: ScriptSchema) -> ValidationResult:
    """
    Validate a script for logical and structural consistency.
    
    Args:
        script: The script to validate
        
    Returns:
        Validation result with any errors
    """
    errors = []
    
    # Check if starting state exists
    if script.starting_state:
        if not any(state.name == script.starting_state for state in script.states):
            errors.append(f"Starting state '{script.starting_state}' not found in states")
    elif script.states:
        # If we have states but no starting state defined, that's an error
        errors.append("No starting state defined for multi-state script")
    
    # Validate state names are unique
    state_names = [state.name for state in script.states]
    duplicate_states = [name for name in set(state_names) if state_names.count(name) > 1]
    if duplicate_states:
        errors.append(f"Duplicate state names found: {', '.join(duplicate_states)}")
    
    # Validate edges refer to valid states
    for edge in script.edges:
        if not any(state.name == edge.from_state for state in script.states):
            errors.append(f"Edge source state '{edge.from_state}' not found in states")
        if not any(state.name == edge.to_state for state in script.states):
            errors.append(f"Edge target state '{edge.to_state}' not found in states")
    
    # Check for orphaned states (no incoming edges except for starting state)
    if script.states and script.edges:
        reachable_states = {script.starting_state} if script.starting_state else set()
        target_states = {edge.to_state for edge in script.edges}
        reachable_states.update(target_states)
        
        for state in script.states:
            if state.name not in reachable_states and state.name != script.starting_state:
                errors.append(f"State '{state.name}' is not reachable from any other state")
    
    # Check for referenced tools that aren't defined
    defined_tools = {tool.name for tool in script.tools}
    for state in script.states:
        for tool_name in state.tools:
            if tool_name not in defined_tools and tool_name not in script.general_tools:
                errors.append(f"Tool '{tool_name}' referenced in state '{state.name}' is not defined")
    
    for tool_name in script.general_tools:
        if tool_name not in defined_tools:
            errors.append(f"General tool '{tool_name}' is not defined")
    
    # Check for empty required fields
    if not script.name:
        errors.append("Script name is required")
    
    for i, state in enumerate(script.states):
        if not state.prompt:
            errors.append(f"State at index {i} is missing prompt content")
    
    return ValidationResult(valid=len(errors) == 0, errors=errors)
