"""
Appointment scheduling script template.
"""
from typing import Dict, Any

from services.llm.script.schema import StateType


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
