"""
Advanced script examples with nodes and edges for complex call flows.
This module serves as a bridge between programmatic script creation and JSON-loaded scripts.
"""
from typing import Dict, Any, List, Optional, Union
import json
from pathlib import Path

from core.logging.setup import get_logger
from services.llm.script.schema import StateType, EdgeCondition, ScriptSchema
from services.llm.script.loader import ScriptLoader
from services.llm.script.parser import ScriptNodeEdgeParser
from services.llm.script.json.generator import JSONScriptGenerator

logger = get_logger(__name__)


async def load_script_from_json(file_path: Union[str, Path]) -> Optional[ScriptSchema]:
  """
  Load a script from a JSON file.

  Args:
      file_path: Path to the JSON script file

  Returns:
      Loaded script schema or None if failed
  """
  return await ScriptLoader.load_from_file(file_path)


async def save_script_to_json(script: Dict[str, Any], output_path: Union[str, Path]) -> bool:
  """
  Save a script dictionary to a JSON file.

  Args:
      script: Script dictionary
      output_path: Path where to save the JSON file

  Returns:
      Whether the operation was successful
  """
  try:
    # Generate output directory if needed
    output_path = Path(output_path) if isinstance(
        output_path, str) else output_path
    output_dir = output_path.parent
    filename = output_path.name

    result = JSONScriptGenerator.export_dict_to_file(
        script, output_dir, filename)
    return result is not None
  except Exception as e:
    logger.error(f"Failed to save script to {output_path}: {e}")
    return False


def create_appointment_script_with_edges() -> Dict[str, Any]:
  """
  Create an appointment scheduling script with explicit nodes and edges for direction control.
  This can be used as a template for constructing scripts programmatically before saving as JSON.

  Returns:
      Script with full node-edge structure
  """
  return {
      "name": "appointment_scheduling_advanced",
      "description": "Advanced script for scheduling appointments with directed flow control",
      "version": "1.0",
      "general_prompt": "You are a helpful scheduling assistant for a medical clinic. Be professional, empathetic, and efficient.",
      "starting_state": "greeting",
      "states": [
          {
              "name": "greeting",
              "type": StateType.INITIAL,
              "prompt": "You are a friendly scheduling assistant. Greet the caller and ask how you can help them today. Remember to introduce yourself as {agent_name}.",
              "description": "Initial greeting state",
              "metadata": {
                  "expected_duration": "short",
                  "required": True
              }
          },
          {
              "name": "collect_information",
              "type": StateType.INFORMATION,
              "prompt": "You are collecting appointment information. Ask for the caller's name, preferred date and time for the appointment, and reason for the appointment. If they've already provided some information, only ask for what's missing.",
              "description": "Collect necessary appointment details",
              "metadata": {
                  "expected_duration": "medium",
                  "required_fields": ["name", "date", "time", "reason"]
              }
          },
          {
              "name": "check_availability",
              "type": StateType.PROCESSING,
              "prompt": "You are checking the calendar for availability. Tell the caller you're checking the schedule. If their requested time is available, sound positive. If not, sound apologetic and suggest 2-3 alternative times close to their requested time.",
              "description": "Checking appointment availability",
              "metadata": {
                  "expected_duration": "short",
                  "simulated_delay": True
              }
          },
          {
              "name": "confirm_details",
              "type": StateType.DECISION,
              "prompt": "Confirm the appointment details with the caller. Read back their name, the date and time, and the reason for the appointment. Ask if everything is correct.",
              "description": "Verify all appointment details are correct",
              "metadata": {
                  "expected_duration": "medium",
                  "decision_point": True
              }
          },
          {
              "name": "schedule_appointment",
              "type": StateType.PROCESSING,
              "prompt": "Thank the caller for confirming the details. Let them know that you're scheduling their appointment now. Tell them they will receive a confirmation via email or text message. Ask if they'd prefer email or text message confirmation.",
              "description": "Process appointment scheduling",
              "metadata": {
                  "expected_duration": "short",
                  "confirmation_required": True
              }
          },
          {
              "name": "handle_confirmation_preference",
              "type": StateType.INFORMATION,
              "prompt": "Ask for their email address or phone number based on their confirmation preference. If they've already provided this information, confirm it with them.",
              "description": "Get preferred contact method",
              "metadata": {
                  "expected_duration": "short",
                  "required_fields": ["contact_method", "contact_info"]
              }
          },
          {
              "name": "closing",
              "type": StateType.TERMINAL,
              "prompt": "Thank the caller for contacting you. Wish them a good day and end the call professionally. Let them know they can call back anytime if they need to reschedule.",
              "description": "End conversation politely",
              "metadata": {
                  "expected_duration": "short",
                  "required": True
              }
          },
          {
              "name": "reschedule",
              "type": StateType.DECISION,
              "prompt": "Ask the caller if they'd like to choose a different time or date. Be accommodating and apologetic that their preferred time is not available.",
              "description": "Handle reschedule request",
              "metadata": {
                  "expected_duration": "medium",
                  "decision_point": True
              }
          }
      ],
      "edges": [
          {
              "from_state": "greeting",
              "to_state": "collect_information",
              "description": "Move to collecting appointment information"
          },
          {
              "from_state": "collect_information",
              "to_state": "check_availability",
              "description": "Check availability once information is collected",
              "condition": {
                  "type": "entity_complete",
                  "value": ["name", "date", "time", "reason"],
                  "operator": "all_present"
              }
          },
          {
              "from_state": "check_availability",
              "to_state": "confirm_details",
              "description": "Time is available, confirm details",
              "condition": {
                  "type": "availability",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "check_availability",
              "to_state": "reschedule",
              "description": "Time not available, offer to reschedule",
              "condition": {
                  "type": "availability",
                  "value": False,
                  "operator": "equals"
              }
          },
          {
              "from_state": "reschedule",
              "to_state": "collect_information",
              "description": "Customer wants to try a different time",
              "condition": {
                  "type": "intent",
                  "value": "reschedule",
                  "operator": "equals"
              }
          },
          {
              "from_state": "reschedule",
              "to_state": "closing",
              "description": "Customer doesn't want to reschedule",
              "condition": {
                  "type": "intent",
                  "value": "cancel",
                  "operator": "equals"
              }
          },
          {
              "from_state": "confirm_details",
              "to_state": "schedule_appointment",
              "description": "Details confirmed, proceed with scheduling",
              "condition": {
                  "type": "confirmation",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "confirm_details",
              "to_state": "collect_information",
              "description": "Details incorrect, collect information again",
              "condition": {
                  "type": "confirmation",
                  "value": False,
                  "operator": "equals"
              }
          },
          {
              "from_state": "schedule_appointment",
              "to_state": "handle_confirmation_preference",
              "description": "Appointment scheduled, handle notification preferences"
          },
          {
              "from_state": "handle_confirmation_preference",
              "to_state": "closing",
              "description": "Notification preferences collected, finish call"
          }
      ],
      "dynamic_variables": {
          "agent_name": "Dr. Smith's Office Assistant",
          "clinic_name": "Smith Family Medical Clinic",
          "clinic_phone": "555-123-4567",
          "business_hours": "Monday through Friday, 9 AM to 5 PM"
      },
      "metadata": {
          "domain": "healthcare",
          "average_duration": "4-5 minutes",
          "success_criteria": "Appointment successfully scheduled with all required information"
      }
  }


async def validate_script_structure(script_data: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
  """
  Validate a script's structure and logical flow.

  Args:
      script_data: Either a script dictionary, a JSON string, or a path to a JSON file

  Returns:
      Dictionary with validation results
  """
  try:
    # Handle different input types
    if isinstance(script_data, (str, Path)) and not isinstance(script_data, dict):
      # Check if it's a file path
      path = Path(script_data)
      if path.exists() and path.is_file():
        script = await ScriptLoader.load_from_file(path)
      else:
        # Try parsing as JSON string
        try:
          script = await ScriptLoader.load_from_string(str(script_data))
        except:
          return {
              "valid": False,
              "errors": ["Input is neither a valid file path nor a valid JSON string"]
          }
    else:
      # Assume it's a dictionary
      script = await ScriptLoader.load_from_dict(script_data)

    if not script:
      return {
          "valid": False,
          "errors": ["Failed to parse script"]
      }

    # Check graph structure
    is_valid, error_message = ScriptNodeEdgeParser.is_valid_graph_structure(
        script.states, script.edges, script.starting_state
    )

    if not is_valid:
      return {
          "valid": False,
          "errors": [error_message]
      }

    # Verify all states referenced in edges exist
    state_names = {state.name for state in script.states}
    invalid_edges = []

    for edge in script.edges:
      if edge.from_state not in state_names:
        invalid_edges.append(
            f"Edge references non-existent from_state: {edge.from_state}")
      if edge.to_state not in state_names:
        invalid_edges.append(
            f"Edge references non-existent to_state: {edge.to_state}")

    if invalid_edges:
      return {
          "valid": False,
          "errors": invalid_edges
      }

    # Check for reachability from starting state
    if not script.starting_state:
      return {
          "valid": False,
          "errors": ["No starting state defined"]
      }

    reachable_states = set()
    states_to_check = [script.starting_state]

    while states_to_check:
      current_state = states_to_check.pop()
      if current_state in reachable_states:
        continue

      reachable_states.add(current_state)

      # Find all states reachable from current state
      for edge in script.edges:
        if edge.from_state == current_state and edge.to_state not in reachable_states:
          states_to_check.append(edge.to_state)

    unreachable_states = state_names - reachable_states
    if unreachable_states:
      return {
          "valid": False,
          "warnings": [f"Unreachable states: {', '.join(unreachable_states)}"]
      }

    return {
        "valid": True,
        "script_name": script.name,
        "state_count": len(script.states),
        "edge_count": len(script.edges)
    }

  except Exception as e:
    return {
        "valid": False,
        "errors": [f"Validation error: {str(e)}"]
    }
