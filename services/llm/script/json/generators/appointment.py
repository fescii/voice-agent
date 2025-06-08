"""
Appointment scheduling script generator.
"""
import json
from typing import Dict, Any


def generate_appointment_script_json() -> str:
  """
  Generate a JSON script for appointment scheduling.

  Returns:
      Script as JSON string
  """
  script = {
      "name": "appointment_scheduling",
      "description": "Script for scheduling appointments with directed flow control",
      "version": "1.0",
      "general_prompt": "You are a helpful scheduling assistant for a medical clinic. Be professional, empathetic, and efficient.",
      "starting_state": "greeting",
      "states": [
          {
              "name": "greeting",
              "type": "initial",
              "prompt": "You are a friendly scheduling assistant. Greet the caller and ask how you can help them today. Remember to introduce yourself as {agent_name}.",
              "description": "Initial greeting state",
              "metadata": {
                  "expected_duration": "short",
                  "required": True
              }
          },
          {
              "name": "collect_information",
              "type": "information",
              "prompt": "You are collecting appointment information. Ask for the caller's name, preferred date and time for the appointment, and reason for the appointment. If they've already provided some information, only ask for what's missing.",
              "description": "Collect necessary appointment details",
              "metadata": {
                  "expected_duration": "medium",
                  "required_fields": ["name", "date", "time", "reason"]
              }
          },
          {
              "name": "check_availability",
              "type": "processing",
              "prompt": "You are checking the calendar for availability. Tell the caller you're checking the schedule. If their requested time is available, sound positive. If not, sound apologetic and suggest 2-3 alternative times close to their requested time.",
              "description": "Checking appointment availability",
              "metadata": {
                  "expected_duration": "short",
                  "simulated_delay": True
              }
          },
          {
              "name": "confirm_appointment",
              "type": "confirmation",
              "prompt": "You are confirming appointment details. Summarize the appointment: name, date, time, and reason. Ask the caller to confirm all details are correct. Be clear and speak slowly when providing the summary.",
              "description": "Confirm appointment details",
              "metadata": {
                  "expected_duration": "short",
                  "confirmation_required": True
              }
          },
          {
              "name": "provide_details",
              "type": "information",
              "prompt": "You are providing appointment details. Give the caller any necessary information: clinic address, what to bring, parking instructions, and any preparation needed. Be thorough but concise.",
              "description": "Provide appointment logistics",
              "metadata": {
                  "expected_duration": "medium",
                  "information_type": "logistics"
              }
          },
          {
              "name": "closing",
              "type": "final",
              "prompt": "You are ending the call. Thank the caller for scheduling their appointment, remind them of the date and time one more time, and let them know they can call back if they need to reschedule.",
              "description": "End call professionally",
              "metadata": {
                  "expected_duration": "short",
                  "required": True
              }
          },
          {
              "name": "reschedule",
              "type": "alternative",
              "prompt": "You are helping reschedule an appointment. Ask when they would prefer to reschedule, check availability for their new preference, and follow the same confirmation process.",
              "description": "Handle rescheduling requests",
              "metadata": {
                  "expected_duration": "medium",
                  "fallback": True
              }
          },
          {
              "name": "escalation",
              "type": "escalation",
              "prompt": "You need to escalate this call. Politely explain that you need to transfer them to someone who can better help with their specific request. Ask them to hold while you transfer the call.",
              "description": "Escalate complex requests",
              "metadata": {
                  "expected_duration": "short",
                  "escalation_reason": "complex_request"
              }
          }
      ],
      "transitions": [
          {
              "from_state": "greeting",
              "to_state": "collect_information",
              "description": "Standard flow to information collection",
              "condition": {
                  "type": "intent",
                  "value": "schedule_appointment",
                  "operator": "equals"
              }
          },
          {
              "from_state": "greeting",
              "to_state": "reschedule",
              "description": "Handle reschedule requests",
              "condition": {
                  "type": "intent",
                  "value": "reschedule",
                  "operator": "equals"
              }
          },
          {
              "from_state": "greeting",
              "to_state": "escalation",
              "description": "Escalate non-scheduling requests",
              "condition": {
                  "type": "intent",
                  "value": "other",
                  "operator": "equals"
              }
          },
          {
              "from_state": "collect_information",
              "to_state": "check_availability",
              "description": "Check availability once info collected",
              "condition": {
                  "type": "information_complete",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "collect_information",
              "to_state": "escalation",
              "description": "Escalate if unable to collect information",
              "condition": {
                  "type": "attempts",
                  "value": 3,
                  "operator": "greater_than"
              }
          },
          {
              "from_state": "check_availability",
              "to_state": "confirm_appointment",
              "description": "Confirm if time is available",
              "condition": {
                  "type": "availability",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "check_availability",
              "to_state": "collect_information",
              "description": "Collect new time if not available",
              "condition": {
                  "type": "availability",
                  "value": False,
                  "operator": "equals"
              }
          },
          {
              "from_state": "confirm_appointment",
              "to_state": "provide_details",
              "description": "Provide details after confirmation",
              "condition": {
                  "type": "confirmation",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "confirm_appointment",
              "to_state": "collect_information",
              "description": "Recollect info if not confirmed",
              "condition": {
                  "type": "confirmation",
                  "value": False,
                  "operator": "equals"
              }
          },
          {
              "from_state": "provide_details",
              "to_state": "closing",
              "description": "End call after providing details",
              "condition": {
                  "type": "details_provided",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "reschedule",
              "to_state": "check_availability",
              "description": "Check availability for new time",
              "condition": {
                  "type": "new_time_provided",
                  "value": True,
                  "operator": "equals"
              }
          },
          {
              "from_state": "escalation",
              "to_state": "closing",
              "description": "End call after escalation",
              "condition": {
                  "type": "escalated",
                  "value": True,
                  "operator": "equals"
              }
          }
      ],
      "dynamic_variables": {
          "agent_name": "Sarah",
          "clinic_name": "Downtown Medical Center",
          "clinic_address": "123 Main Street, Suite 200",
          "clinic_phone": "(555) 123-4567"
      },
      "metadata": {
          "domain": "healthcare",
          "average_duration": "3-5 minutes",
          "success_criteria": "Appointment scheduled with all details confirmed"
      }
  }

  return json.dumps(script, indent=2)
